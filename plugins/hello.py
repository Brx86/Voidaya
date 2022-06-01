from . import logger
from tools import Message
from voidaya import Method


class Plugin(Method):
    def match(self):  # 说 hello 则回复
        return self.on_full_match("hello")

    async def handle(self):
        await self.send_msg(Message.text(f"Hello {self.name}"))
