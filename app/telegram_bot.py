import logging
import threading
from redis import Redis

from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

from utils import Config, MessageDao

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class TelegramBot:
    def __init__(self, chat, *args, **kwargs):
        self.chat = chat
        self.redis = Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            charset="utf-8",
            decode_responses=True
        )

        self.updater = Updater(*args, **kwargs)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(MessageHandler(Filters.text, self.telegram2redis))

        subscribe_thread = threading.Thread(target=self.redis2telegram)
        subscribe_thread.start()

        print("Telegram Bot has been started!")
        self.updater.start_polling()
        self.updater.idle()

    def redis2telegram(self):
        pub_sub = self.redis.pubsub()
        pub_sub.subscribe('discord2telegram')
        for msg in pub_sub.listen():
            if msg.get("type") != "message":
                continue
            message = MessageDao.decode(msg.get('data'))

            # send message
            self.dispatcher.bot.sendMessage(self.chat, Config.MESSAGE_FORMAT.format(
                    message.author.get("first_name"),
                    message.text,
                    "(edited)" if message.edited else "",
            ))

    def telegram2redis(self, update: Update, context: CallbackContext):
        msg = update.message if update.message else update.edited_message

        # only watch for the defined chats
        if msg and msg.chat_id != int(self.chat):
            return

        # create the doa object, serialize it using json and encode it using base64
        message: MessageDao = MessageDao(msg.message_id, **{
            "author": {
                "username": msg.from_user.username,
                "is_bot": msg.from_user.is_bot,
                "first_name": msg.from_user.first_name,
            },
            "text": msg.text,
            "date": msg.date.isoformat(),
            "edited": msg.edit_date.isoformat() if msg.edit_date else None,
        })

        # send data to redis pub-sub
        self.redis.publish("telegram2discord", message.encode())


if __name__ == '__main__':
    TelegramBot(
        chat=Config.TELEGRAM_GROUP_ID,
        token=Config.TELEGRAM_TOKEN
    )
