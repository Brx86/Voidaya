# -*- encoding: utf-8 -*-
"""
@File    :   hello.py
@Time    :   2022/06/03 21:30:15
@Author  :   Ayatale 
@Version :   1.0
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   Hello World
"""


from tools import Message
from voidaya import Method


class Plugin(Method):
    def match(self):  # 说 hello 则回复
        return self.on_full_match("hello")

    async def handle(self):
        return await self.send_msg(
            Message.at(self.uid),
            Message.text(f"Hello {self.name}"),
        )
