from json import dumps

import aiohttp
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from STGB_backend.auth import get_current_active_user
from config import Config
from database import WebUser
from utils.connector import Connector
from utils.schema import MultipleUpdates

router = APIRouter()
ERROR = {"status": "error"}


class AcptMessage(BaseModel):
    text: str


class Message(AcptMessage):
    text: str
    chat_id: int
    user_id: int

    def to_json(self):
        return dumps({"text": self.text, "chat_id": self.chat_id, "user_id": self.user_id})


connector = Connector("send", host=Config.RABBITMQ)


@router.get("/bots")
def get_bots(current_user: WebUser = Depends(get_current_active_user)):
    bots_id = [b.id for b in current_user.bots]
    return {"bots": bots_id}


# @router.get("/{bot_id}/users")
# def get_support_users(bot_id: int, current_user: WebUser = Depends(get_current_active_user)):
#     support_users = User.get_support_users(bot_id)
#     return {'support_users': [{'username': u.username, 'id': u.id} for u in support_users]}


@router.get("/{bot_id}/chats")
def get_chats(bot_id: int, current_user: WebUser = Depends(get_current_active_user)):
    chats = current_user.get_chat(bot_id)
    if chats:
        return {"bot_id": bot_id, "chats": [chat.to_dict_last() for chat in chats]}
    return Response(status_code=403)


@router.get("/messages/{chat_id}")
async def get_messages(chat_id: int, current_user: WebUser = Depends(get_current_active_user)):
    chat = current_user.get_chat_by_id(chat_id)
    if not chat:
        return Response(status_code=403)
    # TODO: Add pagination
    messages = chat.get_all_messages()
    return {"chat_id": chat_id, "messages": [message.to_dict() for message in messages]}


@router.post("/messages/{chat_id}")
async def send_message(chat_id: int, message: AcptMessage, current_user: WebUser = Depends(get_current_active_user)):
    print("CATCH", message.text)
    if not current_user.is_allowed(chat_id=chat_id):
        return Response(status_code=403)
    msg = Message(text=message.text, user_id=current_user.uid, chat_id=chat_id)
    if msg.chat_id != chat_id:
        return ERROR
    if connector.publish(msg.to_json()):
        return {"status": "send"}
    else:
        return ERROR


@router.get("/updates/{chat_id}")  # {user_id}
async def get_updates(chat_id: int, current_user: WebUser = Depends(get_current_active_user)):
    chat = current_user.get_chat_by_id(chat_id)
    if not chat:
        return Response(status_code=403)
    # TODO: Add pagination
    messages = chat.get_all_messages()
    return {"chat_id": chat_id, "messages": [message.to_dict() for message in messages]}


@router.get("/updates", response_model=MultipleUpdates)
async def get_all_updates(current_user: WebUser = Depends(get_current_active_user)):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{Config.UPDATER_URL}/{current_user.uid}/info") as response:

            if response.status == 502:
                return Response(status_code=502)
            else:
                data = await response.json()
                return MultipleUpdates(**data)
