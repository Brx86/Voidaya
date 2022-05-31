from voidaya import Plugin, text


class PatchPlugin(Plugin):
    def match(self):  # 说 hello 则回复
        return self.on_full_match("hello")

    async def handle(self):
        await self.send_msg(text(f"Hello {self.name}"))
