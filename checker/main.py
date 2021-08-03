import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from update_checker import Checker

from utils.connector import NotifyListener
from utils.schema import MultipleUpdates

TIMEOUT = 5
checker = Checker()
connector = NotifyListener(checker, consumer_tag='notify')

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
loop = None


@app.get('/{user_id}/info', response_model=MultipleUpdates)
async def subscribe(user_id: int):
    info = checker.get_info(user_id)
    if info:
        return info

    current_info = checker.add_current_listener(user_id)
    result = asyncio.wait_for(current_info, TIMEOUT)
    try:
        return await result
    except asyncio.exceptions.TimeoutError:
        checker.cancel_listener(user_id, current_info)
        return Response(status_code=502)


@app.post('/{user_id}/unsubscribe')
def unsubscribe(user_id: int):
    checker.remove_listener(user_id)
    return Response()


@app.on_event('startup')
def run_connector():
    global loop
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, connector.start)


@app.on_event('shutdown')
def stop_connector():
    connector.stop()


uvicorn.run(app, host="0.0.0.0", port=8001)
# if __name__ == '__main__':
#     checker.add_listener(8)
#     u = User(uid=1, username='user')
#     m = Message(id=1, text='text', time=datetime.datetime(2021, 1, 1, 1, 1, 31),
#                 user=u)
#     chat = Chat(chat_id=1, messages=[m])
#     u1 = Update(bot_id=1, chats=[chat])
#     nu = NotifyUpdate(user_id=8, updates=[u1])
#     mu = MultipleNotifyUpdates(updates=[nu])
#     checker.add_information(mu)
