from json import dumps

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import Handler, Message, Bot, init_db
from utils import Connector

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


class AcptMessage(BaseModel):
    text: str
    chat_id: int
    bot_id: int
    # TODO: Change type
    time: str

    def to_json(self):
        return dumps({"text": self.text, "chat_id": self.chat_id, "bot_id": self.bot_id,
                      "time": self.time})


connector = Connector('send')


@Handler.request_decorator
@app.get("/bots")
def get_bots():
    bots = Bot.get_all()
    bots_id = [b.id for b in bots]
    return {"bots": bots_id}


@app.get("/{bot_id}/chats")
def get_chats(bot_id: int):
    messages = Bot.get_messages(bot_id)
    return {"bot_id": bot_id, "messages": [message.to_dict() for message in messages]}


@app.get("/{bot_id}/messages/{user_id}")
async def get_messages(bot_id: int, user_id: int):
    messages = Message.get_messages(bot_id, user_id)
    return {"user_id": user_id, "messages": [message.to_dict() for message in messages]}


@app.post("/{bot_id}/messages/{user_id}")
async def send_message(bot_id: int, user_id: int, msg: AcptMessage):
    print("CATCH", msg.text)
    if connector.publish(msg.to_json()):
        return {"status": "send"}
    else:
        return {"status": "error"}
