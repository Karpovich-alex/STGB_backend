import asyncio
import datetime
import threading
from typing import Dict, List, Optional

from pydantic import BaseModel


# {'text': self.text, 'time': self.time, 'chat_id': self.chat_id, 'user_id': self.user_id,
#                 'username': self.user.username}
class Message(BaseModel):
    text: str
    time: datetime.datetime
    user_id: int
    username: str
    chat_id: int


class Chat(BaseModel):
    chat_id: int
    messages: List[Message]

    def __init__(self, message: Dict):
        chat_id = message.get('chat_id', 0)
        super(Chat, self).__init__(chat_id=chat_id, messages=[message])

    def add_msg(self, message: Dict):
        self.messages.append(Message(**message))


class Checker:
    def __init__(self):
        self._listeners = [2, ]
        self._information: Dict[int, Dict[int, List[Message]]] = {}
        self._current_listeners: Dict[int, List[asyncio.Future]] = {}
        self._info_lock = threading.RLock()
        self._current_listeners_lock = threading.RLock()

    def check_listener(self, user_id):
        if user_id in self._listeners:
            return True
        return False

    @staticmethod
    def _update_info(old_info: Dict, new_info: Dict):
        chat = Chat(new_info)
        if not old_info:
            return {chat.chat_id: chat.messages}

        if chat.chat_id in old_info.keys():
            old_info_chat_messages = old_info.get(chat.chat_id) or []
            old_info_chat_messages += chat.messages
            old_info[chat.chat_id] = old_info_chat_messages
        else:
            old_info[chat.chat_id] = chat.messages
        return old_info

    @staticmethod
    def parse_message(message) -> Dict:
        chat = Chat(message)
        return {chat.chat_id: chat.messages}

    @property
    def information(self):
        return self._information

    def check_current_listeners(self, user_id):
        return user_id in self._current_listeners.keys()

    def add_information(self, message: Dict, users: List[int]):
        for user_id in users:
            self._add_information(message, user_id)

    def _add_information(self, message, user_id):
        with self._current_listeners_lock:
            current_listeners = self._current_listeners.pop(user_id, None)
            if current_listeners:
                for current_listener in current_listeners:
                    try:
                        current_listener.set_result(self.export_chat(self.parse_message(message)))
                    except Exception as exc:
                        print(exc)
                    print(current_listener)
                return

        if self.check_listener(user_id):
            with self._info_lock:
                self._information[user_id] = self._update_info(self._information.get(user_id, {}), message)

    def get_info(self, user_id) -> Optional[Dict]:
        if user_id in self._information.keys():
            info = self._information.pop(user_id)
            output_data = self.export_chat(info)
            return output_data
        self.add_listener(user_id)

    @staticmethod
    def export_chat(info) -> Dict:
        output_data = {}
        for chat_id, messages in info.items():
            output_data['chat_id'] = chat_id
            output_data['messages'] = [msg.dict() for msg in messages]
        return output_data

    def check_info(self, user_id):
        return user_id in self._information.keys()

    def add_listener(self, user_id):
        if not self.check_listener(user_id):
            self._listeners.append(user_id)

    def remove_listener(self, user_id):
        if user_id in self._listeners:
            self._listeners.remove(user_id)
        if user_id in self._information:
            self._information.pop(user_id)

    def add_current_listener(self, user_id, loop):
        # TODO: Add timeoit to store user_id
        fut = loop.create_future()
        self._current_listeners[user_id] = self._current_listeners.get(user_id, []) + [fut]
        return fut

    def cancel_listener(self, user_id, fut):
        with self._current_listeners_lock:
            if user_id in self._current_listeners.keys():
                try:
                    self._current_listeners.get(user_id, []).remove(fut)
                except ValueError:
                    pass
                if not self._current_listeners.get(user_id):
                    self._current_listeners.pop(user_id)
