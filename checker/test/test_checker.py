import datetime
import unittest

from STGB_backend.checker.update_checker import Checker
from utils.schema import Message, Chat, NotifyUpdate, User, Update, MultipleNotifyUpdates, MultipleUpdates

message = {'id': 1, 'text': 'text', 'time': '2011-11-11 11:11:11', 'chat_id': 1, 'user_id': 1,
           'username': 'test_username'}


class ExportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = Checker()

    def test_export_one(self):
        self.checker.add_listener(1)
        u = User(uid=1, username='user')
        m = Message(id=1, text='text', time=datetime.datetime(2021, 1, 1, 1, 1, 31),
                    user=u)
        chat = Chat(chat_id=1, messages=[m])
        u1 = Update(bot_id=1, chats=[chat])
        nu = NotifyUpdate(user_id=1, updates=[u1])
        mu = MultipleNotifyUpdates(updates=[nu])
        self.checker.add_information(mu)
        info = self.checker.get_info(1)
        self.assertEqual(MultipleUpdates(updates=[u1]), info)

        muu = MultipleUpdates(updates=[u1])

    def test_multiple_updates(self):
        u = User(uid=1, username='user')
        m = Message(id=1, text='text', time=datetime.datetime(2021, 1, 1, 1, 1, 31),
                    user=u)
        chat = Chat(chat_id=1, messages=[m])
        u1 = Update(bot_id=1, chats=[chat])
        nu = NotifyUpdate(user_id=1, updates=[u1])
        mu = MultipleNotifyUpdates(updates=[nu])

    def test_export_two(self):
        self.checker.add_listener(1)
        u = User(uid=1, username='user')
        m = Message(id=1, text='text', time=datetime.datetime(2021, 1, 1, 1, 1, 31),
                    user=u)

        ch1 = Chat(chat_id=1, messages=[m])
        u1 = Update(bot_id=1, chats=[ch1])
        nu1 = NotifyUpdate(user_id=1, updates=[u1])
        mu1 = MultipleNotifyUpdates(updates=[nu1])
        self.checker.add_information(mu1)

        ch2 = Chat(chat_id=2, messages=[m])
        u2 = Update(bot_id=1, chats=[ch2])
        nu2 = NotifyUpdate(user_id=1, updates=[u2])
        mu2 = MultipleNotifyUpdates(updates=[nu2])
        self.checker.add_information(mu2)

        info = self.checker.get_info(1)
        u3 = Update(bot_id=1, chats=[ch1, ch2])
        self.assertEqual([u3], info)

    def test_listeners(self):
        self.assertFalse(self.checker.check_listener(1))
        self.checker.add_listener(1)
        self.assertTrue(self.checker.check_listener(1))
        self.checker.remove_listener(1)
        self.assertTrue(self.checker.check_listener(1))

    def test_current_listeners(self):
        self.assertFalse(self.checker.check_current_listeners(1))
        self.checker.add_current_listener(1)
        self.assertTrue(self.checker.check_current_listeners(1))

    def test_parse_message(self):
        parsed_message = Chat.parse(message)
        self.assertEqual(self.checker.parse_message(message), parsed_message)

    # def test_add_update(self):
    #     update = NotifyUpdate()
