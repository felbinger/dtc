import base64
import json
from datetime import datetime
from typing import Dict, Union
from os import getenv


class Config:
    DISCORD_TOKEN = getenv("DISCORD_TOKEN")
    DISCORD_CHANNEL_ID = getenv("DISCORD_CHANNEL_ID")
    TELEGRAM_TOKEN = getenv("TELEGRAM_TOKEN")
    TELEGRAM_GROUP_ID = getenv("TELEGRAM_GROUP_ID")
    MESSAGE_FORMAT = '{}: {}'
    REDIS_HOST = getenv("REDIS_HOST", "localhost")
    REDIS_PORT = getenv("REDIS_PORT", 6379)
    REDIS_DB = getenv("REDIS_DB", 0)


class MessageDao:
    def __init__(self, message_id, author: dict, text: str, date: datetime, edited: datetime):
        self.message_id: int = message_id
        self.author: Dict[str, Union[str, bool]] = author
        self.text: str = text
        self.date: datetime = date
        self.edited: datetime = edited

    def json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def encode(self) -> bytes:
        return base64.b64encode(self.json().encode("utf8"))

    @staticmethod
    def decode(data: Union[bytes, str]) -> "MessageDao":
        if isinstance(data, bytes):
            data = data.decode()
        return MessageDao(**json.loads(base64.b64decode(data)))
