import asyncio
import threading
from typing import Dict, List, Optional

from utils.schema import Chat, NotifyUpdate, MultipleNotifyUpdates, MultipleUpdates


class Checker:
    def __init__(self):
        self._listeners = []
        self._updates = MultipleNotifyUpdates()
        self._current_listeners: Dict[int, List[asyncio.Future]] = {}
        self._info_lock = threading.RLock()
        self._current_listeners_lock = threading.RLock()

    @property
    def updates(self):
        return self._updates

    @staticmethod
    def parse_message(message) -> Dict:
        chat = Chat.parse(message)
        return {chat.chat_id: chat.messages}

    def check_current_listeners(self, user_id):
        return user_id in self._current_listeners.keys()

    def check_listener(self, user_id):
        if user_id in self._listeners:
            return True
        return False

    def add_information(self, nupdates: MultipleNotifyUpdates):
        for update in nupdates.updates:
            self._add_information(update)

    def _add_information(self, update: NotifyUpdate):
        with self._current_listeners_lock:
            current_listeners = self._current_listeners.pop(update.user_id, None)
            if current_listeners:
                for current_listener in current_listeners:
                    current_listener.set_result(update)
                return

        if self.check_listener(update.user_id):
            with self._info_lock:
                self._updates.append(update)

    def get_info(self, user_id) -> Optional[MultipleUpdates]:
        if self._updates.contain(user_id):
            user_notify = self._updates.get_updates_for(user_id).sort()
            return MultipleUpdates(updates=user_notify.updates)
        self.add_listener(user_id)

    def check_info(self, user_id):
        return self._updates.contain(user_id)

    def add_listener(self, user_id):
        if not self.check_listener(user_id):
            self._listeners.append(user_id)

    def remove_listener(self, user_id):
        if user_id in self._listeners:
            self._listeners.remove(user_id)
        if self._updates.contain(user_id):
            self._updates.remove(user_id)

    def add_current_listener(self, user_id):
        # TODO: Add timeout to store user_id
        loop = asyncio.get_event_loop()
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
