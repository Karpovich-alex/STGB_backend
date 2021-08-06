from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from STGB_backend.WebhookWorker import WebhookWorker
from STGB_backend.auth import get_current_active_user
from database import Bot
from database import WebUser
from utils.schema import CreateBotData, ExportBot, ExportBots

router = APIRouter()
webhook_worker = WebhookWorker()


def get_bot(token, current_user: WebUser = Depends(get_current_active_user)):
    bot = current_user.get_bot(token=token)
    if not bot:
        raise HTTPException(status_code=400)
    return bot


@router.get('/all', response_model=ExportBots)
async def get_all_bots(current_user: WebUser = Depends(get_current_active_user)):
    bots = current_user.bots
    return ExportBots(bots=bots)


@router.post('/{api_token}/stop')
async def stop_bot(bot=Depends(get_bot)):
    stopped = await webhook_worker.delete_webhook(bot.token)
    if not stopped:
        raise HTTPException(status_code=400)
    else:
        return Response(status_code=200)


@router.post('/{api_token}/start')
async def start_bot(bot=Depends(get_bot)):
    started = await webhook_worker.set_webhook(bot.token)
    if not started:
        raise HTTPException(status_code=400)
    else:
        return Response(status_code=200)


@router.post('/{api_token}/delete')
async def delete_bot(bot=Depends(get_bot)):
    started = await webhook_worker.set_webhook(bot.token, bot.api_token)
    if not started:
        raise HTTPException(status_code=400)
    else:
        return Response(status_code=200)


@router.post('/add')
async def add_bot(bot_data: CreateBotData, current_user: WebUser = Depends(get_current_active_user)):
    bot_info = await webhook_worker.get_bot_info(bot_data.token)
    if not bot_info:
        raise HTTPException(status_code=400, detail='Incorrect bot token')
    bot = Bot(messenger=bot_data.messenger, nickname=bot_data.nickname, token=bot_data.token, messenger_id=bot_info.id,
              messenger_name=bot_info.username)
    # if not created:
    #     raise HTTPException(status_code=500)
    current_user.add_bot(bot)
    return ExportBot.from_orm(bot)


if __name__ == '__main__':
    from fastapi import FastAPI
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    app = FastAPI()
    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix='/bot')
    uvicorn.run(app, host="0.0.0.0", port=8000)
