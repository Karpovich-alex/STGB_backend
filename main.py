from fastapi import FastAPI

from fastapi import FastAPI

from database import Handler, Message, Bot, init_db

init_db()
app = FastAPI()


@Handler.request_decorator
@app.get("/bots")
def get_bots():
    bots = Bot.get_all()
    bots_id = [b.id for b in bots]
    return {"BOTS": bots_id}


@app.get("/{bot_id}/chats")
def read_item(bot_id: int):
    messages = Bot.get_messages(bot_id)
    return {"bot_id": bot_id, "messages": [message.to_dict() for message in messages]}


@app.get("/{bot_id}/{user_id}")
async def read_item(bot_id: int, user_id: int):
    messages = Message.get_messages(bot_id, user_id)
    return {"user_id": user_id, "messages": [message.to_dict() for message in messages]}
