# -*- encoding: utf-8 -*-
"""
@File    :   kemo.py
@Time    :   2022/06/03 21:30:40
@Author  :   Ayatale 
@Version :   1.0
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   随机兽耳酱
"""


from . import logger
from tools import Message
from voidaya import Method
from random import randint

base_url = "https://ayatale.coding.net/p/picbed/d/kemo/git/raw/master"


class Plugin(Method):
    def match(self):  # 检测命令/kemo, /k, /kk
        return self.on_command(["/kemo", "/k", "/kk"])

    async def handle(self):
        if len(self.args) == 2 and self.args[1].isdigit():
            n = int(self.args[1])
            if n < 1:
                n = 1
            elif n > 5:
                n = 5
        else:
            n = 1
        msg_list = []
        for _ in range(n):
            while self.db.check_times(picname := f"{randint(1, 696)}.jpg"):
                logger.info(f"{picname} is already in list.")
            if self.db.check_limit(name := f"kemo:{self.gid}:{self.uid}"):
                msg_list.append(Message.image(f"{base_url}/{picname}"))
            else:
                logger.warning(f"[{name}] has reached the limit.")
                break
        if msg_list:
            return await self.send_msg(*msg_list)
        return await self.send_msg("你的访问太频繁了，休息一下吧")
