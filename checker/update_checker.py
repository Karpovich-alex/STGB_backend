import asyncio
from typing import Dict, Set

from utils.schema import NotifyUpdate, MultipleNotifyUpdates

TIMEOUT = 5


class Updater:
    def __init__(self):
        self._listeners: Dict[int, Set[int, asyncio.Future]] = {}
        self._listeners_lock = asyncio.Lock()
        self._loop = asyncio.get_event_loop()

    async def check_update(self, user_id):
        async with self._listeners_lock:
            listeners_num, future = self._listeners.get(user_id, {0, self._loop.create_future()})
            listeners_num += 1
            self._listeners[user_id] = {listeners_num, future}
        try:
            result = await asyncio.wait_for(future, timeout=TIMEOUT)
        except asyncio.exceptions.TimeoutError:
            result = False
        await self._check_listener(user_id)
        return result

    async def _check_listener(self, user_id):
        async with self._listeners_lock:
            listeners_num, future = self._listeners[user_id]
            listeners_num -= 1
            if listeners_num == 0:
                self._listeners.pop(user_id)
            else:
                self._listeners[user_id] = {listeners_num, future}

    async def handle_update(self, user_id, update: NotifyUpdate):
        async with self._listeners_lock:
            if user_id in self._listeners:
                _, future = self._listeners.get(user_id)
                future.set_result(update)

    async def handle_updates(self, updates: MultipleNotifyUpdates):
        for update in updates:
            await self.handle_update(update.user_id, update.updates)
