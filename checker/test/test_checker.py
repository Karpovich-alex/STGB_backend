import unittest
import asyncio
import unittest

from STGB_backend.checker.update_checker import Updater
from utils.schema import Chat

message = {'id': 1, 'text': 'text', 'time': '2011-11-11 11:11:11', 'chat_id': 1, 'user_id': 1,
           'username': 'test_username'}


class UpdaterTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.updater = Updater()

    async def test_export_one(self):
        update = asyncio.create_task(self.updater.check_update(1))
        await asyncio.gather(update, self.updater.handle_update(1, 'update'))
        self.assertEqual(update.result(), 'update')

    async def test_multiple_updates(self):
        update1 = asyncio.create_task(self.updater.check_update(1))
        update2 = asyncio.create_task(self.updater.check_update(2))
        await asyncio.gather(update1, update2, self.updater.handle_update(1, 'update'))
        self.assertEqual(update1.result(), 'update')
        self.assertEqual(update2.result(), False)

    async def test_export_two(self):
        update1 = asyncio.create_task(self.updater.check_update(1))
        update2 = asyncio.create_task(self.updater.check_update(2))
        await asyncio.gather(update1, update2, self.updater.handle_update(1, 'update1'),
                             self.updater.handle_update(2, 'update2'))
        self.assertEqual(update1.result(), 'update1')
        self.assertEqual(update2.result(), 'update2')

    async def test_many_listeners(self):
        update1 = asyncio.create_task(self.updater.check_update(1))
        update2 = asyncio.create_task(self.updater.check_update(1))
        await asyncio.gather(update1, update2, self.updater.handle_update(1, 'update1'))
        self.assertEqual(update1.result(), 'update1')
        self.assertEqual(update2.result(), 'update1')

    def test_current_listeners(self):
        self.assertFalse(self.checker.check_current_listeners(1))
        self.checker.add_current_listener(1)
        self.assertTrue(self.checker.check_current_listeners(1))

    def test_parse_message(self):
        parsed_message = Chat.parse(message)
        self.assertEqual(self.checker.parse_message(message), parsed_message)

    # def test_add_update(self):
    #     update = NotifyUpdate()
