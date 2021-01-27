from discord import Client, Message, TextChannel, Forbidden, HTTPException
from discord.ext import tasks
from aioredis import create_redis_pool, Channel

from utils import Config, MessageDao


class DiscordBot(Client):
    def __init__(self, chat, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat = chat
        self.redis = None

    async def on_ready(self):
        print("Discord Bot has been started!")
        self.redis = await create_redis_pool(f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}')
        self.redis2discord.start()

    async def on_message(self, message: Message):
        if message.author == self.user:
            return

        if message.channel != self.get_channel(int(self.chat)):
            return

        # send data to redis pub-sub
        msg: MessageDao = MessageDao(message.id, text=message.content, author={
            "username": message.author.mention,
            "first_name": message.author.display_name,
            "is_bot": message.author.bot,
        }, date=message.created_at.isoformat(), edited=message.edited_at.isoformat() if message.edited_at else None)

        if not self.redis:
            print("Redis not initialized!")
            return

        await self.redis.publish("discord2telegram", msg.encode())

    @tasks.loop(seconds=1, count=1)
    async def redis2discord(self):
        channel: TextChannel = self.get_channel(int(self.chat))
        if not channel:
            return

        redis_channel: Channel = (await self.redis.subscribe('telegram2discord'))[0]
        while await redis_channel.wait_message():
            data = await redis_channel.get()
            message = MessageDao.decode(data)

            # send message
            try:
                await channel.send('{}: {} {}'.format(
                    message.author.get("first_name"),
                    message.text,
                    "(edited)" if message.edited else "",
                ))
            except (Forbidden, HTTPException):
                print(f"Unable to send in {channel.name}!")


if __name__ == '__main__':
    discord = DiscordBot(Config.DISCORD_CHANNEL_ID)
    discord.run(Config.DISCORD_TOKEN)
