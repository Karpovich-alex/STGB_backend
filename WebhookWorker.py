from typing import Optional, Dict, Any

import aiohttp

from config import Config
from utils.tg_schema import TGUser


class WebhookWorker:
    def __init__(self, ):
        self.base_url = 'https://api.telegram.org/bot'
        self.webhook_url = Config.TELEGRAM_WEBHOOK_URL

    async def _post(self, endpoint, token, *, params=None, auth=False) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            if auth:
                files = {'key': open(Config.CERTIFICATE_PATH, 'rb')}
            else:
                files = {}
            async with session.post(f"{self.base_url}{token}/{endpoint}", params=params, data=files) as response:
                data = await response.json()
                return data

    @staticmethod
    def validate_webhook_data(data):
        if not data['ok'] or data['ok'] == False:
            return False
        return True

    async def set_webhook(self, token):
        params = {'url': self.webhook_url + str(token)}
        data = await self._post('setWebhook', token, params=params, auth=True)
        return self.validate_webhook_data(data)

    async def delete_webhook(self, token):
        data = await self._post('deleteWebhook', token)
        return self.validate_webhook_data(data)

    async def get_bot_info(self, token) -> Optional[TGUser]:
        data = await self._post('getMe', token)
        if not data['ok']:
            return
        return TGUser(**data['result'])

    async def send_message(self, token, text: str, chat_id: int):
        result = await self._post('sendMessage', token, params={'chat_id': chat_id, 'text': text})
        # {'ok': True, 'result': {'message_id': 726, 'from': {'id': 929998127, 'is_bot': True, 'first_name': 'Test911000_bot', 'username': 'Test911000_bot'}, 'chat': {'id': 68658464, 'first_name': 'Alex', 'username': 'sash_ka', 'type': 'private'}, 'date': 1628375617, 'text': 'hello world!'}}
        return result
