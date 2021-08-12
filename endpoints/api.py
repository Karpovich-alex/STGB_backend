import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from config import Config
from database import WebUser
from utils.aio_connector import AIONotifyListener, AIOConnector
from utils.schema import MultipleUpdates, Update, Chat, WebMessage
from .auth import get_current_active_user
from ..checker import Updater

router = APIRouter()
updater = Updater()
connector = AIOConnector("send", host=Config.RABBITMQ)
update_listener = AIONotifyListener(updater)

ERROR = {"status": "error"}


class AcptMessage(BaseModel):
    text: str


@router.get("/chats")
def get_chats(current_user: WebUser = Depends(get_current_active_user)):
    updates = [

        Update(
            bot_id=bot.id,
            chats=[
                Chat(
                    user=chat.user,
                    id=chat.id,
                    messages=[chat.last_message])
                for chat in current_user.get_chat(bot.id)
            ]
        )
        for bot in current_user.bots
    ]
    return MultipleUpdates(
        updates=updates
    ).dict()


@router.get("/{bot_id}/chats")  # , response_model=MultipleUpdates
def get_bot_chats(bot_id: int, current_user: WebUser = Depends(get_current_active_user)):
    chats = current_user.get_chat(bot_id)
    if chats:
        return MultipleUpdates(
            updates=[
                Update(bot_id=bot_id, chats=[
                    Chat(user=chat.user, id=chat.id, messages=[chat.last_message]) for chat in chats
                ])
            ]
        ).dict()
    return Response(status_code=403)


@router.get("/messages/{bot_id}/{chat_id}")
async def get_messages(bot_id: int, chat_id: int, current_user: WebUser = Depends(get_current_active_user)):
    if not (current_user.is_allowed(chat_id=chat_id) and current_user.is_allowed(bot_id=bot_id)):
        return Response(status_code=403)
    chat = current_user.get_chat_by_id(chat_id)

    # TODO: Add pagination
    return MultipleUpdates(updates=[Update(bot_id=bot_id, chats=[chat])]).dict()
    # return {"chat_id": chat_id, "messages": [message.to_dict() for message in messages]}


@router.post("/messages/{chat_id}")
async def send_message(chat_id: int, message: AcptMessage, current_user: WebUser = Depends(get_current_active_user)):
    print("CATCH", message.text)
    if not current_user.is_allowed(chat_id=chat_id):
        return Response(status_code=403)
    msg = WebMessage(text=message.text, chat_id=chat_id, user=current_user)
    if msg.chat_id != chat_id:
        return ERROR
    result = await connector.publish(msg.json(exclude_none=True, by_alias=True))
    if result:
        return {"status": "send"}
    else:
        return ERROR


# TODO: apply responce model
@router.get("/updates")  # , response_model=MultipleUpdates
async def get_all_updates(current_user: WebUser = Depends(get_current_active_user)):
    data = await updater.check_update(current_user.uid)
    if data:
        return data


# update_listener_task = asyncio.create_task(update_listener.start())
# tasks = [update_listener_task]


@router.on_event('startup')
def run_connector():
    update_listener_task = asyncio.create_task(update_listener.start())
    connector_task = asyncio.create_task(connector.start())
    asyncio.ensure_future(update_listener_task)
    asyncio.ensure_future(connector_task)

    # loop = asyncio.get_running_loop()
    # loop.run_until_complete(connector.start())


@router.on_event('shutdown')
def stop_connector():
    pass
