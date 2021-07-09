import logging
from json import dumps

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import Config
from database import Bot, init_db, Chat, User
from utils.connector import Connector

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
init_db()
app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ERROR = {"status": "error"}


class AcptMessage(BaseModel):
    text: str
    chat_id: int
    user_id: int
    # TODO: Change type
    time: str

    def to_json(self):
        return dumps({"text": self.text, "chat_id": self.chat_id, "time": self.time, "user_id": self.user_id})


connector = Connector("send", host=Config.RABBITMQ)


@app.get("/bots")
def get_bots():
    bots = Bot.get_all()
    bots_id = [b.id for b in bots]
    return {"bots": bots_id}


@app.get("/{bot_id}/users")
def get_support_users(bot_id: int):
    support_users = User.get_support_users(bot_id)
    return {'support_users': [{'username': u.username, 'id': u.id} for u in support_users]}


@app.get("/{bot_id}/chats")
def get_chats(bot_id: int):
    chats = Bot.get_chats(bot_id)
    return {"bot_id": bot_id, "chats": [chat.to_dict_last() for chat in chats]}


@app.get("/messages/{chat_id}")
async def get_messages(chat_id: int):
    chat = Chat.get_chat(chat_id)
    if not chat:
        return {"status": "error"}
    messages = chat.get_all_messages()
    return {"chat_id": chat_id, "messages": [message.to_dict() for message in messages]}


@app.post("/messages/{chat_id}")
async def send_message(chat_id: int, msg: AcptMessage):
    print("CATCH", msg.text)
    if msg.chat_id != chat_id:
        return ERROR
    if connector.publish(msg.to_json()):
        return {"status": "send"}
    else:
        return ERROR


@app.get("/updates/{user_id}")
async def get_updates(user_id: int):
    pass


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
