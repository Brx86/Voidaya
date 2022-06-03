# -*- encoding: utf-8 -*-
"""
@File    :   water.py
@Time    :   2022/06/03 21:41:16
@Author  :   Ayatale 
@Version :   1.0
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   水群发言次数排行榜
"""


import os, re, json, time, aiofiles
from . import PATH, logger
from tools import Message
from voidaya import Method
from collections import Counter


class Plugin(Method):
    def match(self):  # 说 hello 则回复
        return self.on_full_match("/💦")

    async def update(self, gid):
        data = await self.call_api("get_group_member_list", {"group_id": gid})
        if data:
            user_dict = {}
            for u in data["data"]:
                user_dict[u["user_id"]] = u["card"] if u["card"] else u["nickname"]
            async with aiofiles.open(PATH / "src" / f"{gid}.json", "w") as f:
                json.dump(user_dict, f)
            logger.success(f"{gid} get_group_member_list success!")
        else:
            logger.warning(err := f"{gid} get_group_member_list failed.")
            return err

    async def count_msg(self, gid):
        start_time = time.time()
        logpath = f"/home/aya/git/ayabot2/logs/{time.strftime('%Y-%m-%d')}.log"
        group_data = PATH / "src" / f"{gid}.json"
        logger.info(f"Log path: {logpath} group_data: {group_data}")
        logger.info(f"Group data: {group_data}")
        if not os.path.exists(group_data):
            await self.update(gid)
        with open(group_data, "r") as f:
            user_dict = json.load(f)
        with open(logpath, "r") as f:
            raw_msg = f.read()
        pattern = re.compile(f"{gid}-(\d*):")
        qqnum_list = pattern.findall(raw_msg)
        print(f"Reading {len(qqnum_list)} messages...\n")
        qq_count = sorted(
            dict(Counter(qqnum_list)).items(),
            key=lambda x: (x[1], x[0]),
            reverse=True,
        )
        if qq_count:
            msg = f"今日水比排行榜Top10:\n"
            cl = qq_count[:10] if len(qq_count) >= 10 else qq_count
            m = 0
            for k, v in cl:
                m += 1
                username = user_dict.get(k) if user_dict.get(k) else k
                msg = f"{msg}第{m}名: {username}\n       发言{v}条\n"
            return f"{msg}活跃人数: {len(qq_count)}人\n发言总数: {len(qqnum_list)}条\n计算用时: {time.time()-start_time:.3f}s"
        return "未统计本群信息，排行榜为空"

    async def handle(self):
        if len(self.args) > 1:
            if self.args[1] == "test":
                return await self.count_msg(1136462265)
            elif self.args[1].isdigit():
                await self.update(self.args[1])
        return await self.count_msg(self.gid)
