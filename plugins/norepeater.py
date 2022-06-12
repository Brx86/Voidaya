# -*- encoding: utf-8 -*-
"""
@File    :   repeater.py
@Time    :   2022/06/12 15:23:42
@Author  :   Ayatale 
@Version :   1.0
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   自动打断复读
"""

from . import logger
from voidaya import Method


class Plugin(Method):
    def match(self):  # 说 hello 则回复
        if self.gid in [204097403, 718125729]:
            kv = self.db.get(name := f"repeat:{self.gid}")
            if kv is None or kv[0] != self.raw:
                self.db.update(name, [self.raw, 1], log=False)
            else:
                self.db.update(name, [kv[0], kv[1] + 1], log=False)
            if self.db.get(name)[1] == 2:
                logger.warning(f"{self.gid}({self.name})正在复读！")
                return True
        return False

    async def handle(self):
        self.db.data.pop(f"repeat:{self.gid}")
        return await self.send_msg(f"{self.stime} 打断复读！")
