from tools import Message
from voidaya import Method
from random import randint


class Plugin(Method):
    def match(self):  # 说 hello 则回复
        return self.on_command("/kemo", aliases=["/k", "/kk"])

    async def handle(self):
        if len(self.args) == 2 and self.args[1].isdigit():
            n = int(self.args[1])
            if n < 1:
                n = 1
            elif n > 5:
                n = 5
        else:
            n = 1
        kemo_list = []
        base_url = "https://ayatale.coding.net/p/picbed/d/kemo/git/raw/master"
        for _ in range(n):
            kemo_list.append(Message.image(f"{base_url}/{randint(1,696)}.jpg"))
        await self.send_msg(*kemo_list)
