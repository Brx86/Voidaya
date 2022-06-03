# -*- encoding: utf-8 -*-
"""
@File    :   nya.py
@Time    :   2022/06/03 21:31:37
@Author  :   Ayatale 
@Version :   1.0
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   随机猫羽雫(本地图库))
"""


import os
from tools import Message
from voidaya import Method
from random import choice

nya_path = "/home/aya/Pictures/nyacat"
nya_list = os.listdir(nya_path)


class Plugin(Method):
    def match(self):  # 检测命令/nya
        return self.on_command(["/nya"])

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
            msg_list.append(Message.image(f"file://{nya_path}/{choice(nya_list)}"))
        await self.send_msg(*msg_list)
