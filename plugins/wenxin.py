#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   vilg.py
@Time    :   2022/09/09 19:23:23
@Author  :   Ayatale 
@Version :   1.3
@Contact :   ayatale@qq.com
@Github  :   https://github.com/brx86/
@Desc    :   文心模型
"""


from . import logger
from tools import Message
from voidaya import Method
from random import choice
import time, httpx, asyncio

WENXIN_AK = "3RUtTrEVmklgxxxxxxxxxxxxxxxxxxxx"
WENXIN_SK = "6H2GzmqHRhsxxxxxxxxxxxxxxxxxxxxx"

# 6种生成风格的名称
style_list = [
    "水彩",
    "油画",
    "粉笔画",
    "卡通",
    "蜡笔画",
    "儿童画",
]


class Plugin(Method):
    # 获取access_token
    async def get_token(self):
        url = "https://wenxin.baidu.com/younger/portal/api/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": WENXIN_AK,
            "client_secret": WENXIN_SK,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with httpx.AsyncClient(verify=False, timeout=None) as client:
            return (await client.post(url, data=data, headers=headers)).json()["data"]

    # 获取绘画的任务id
    async def get_taskId(self, text, style):
        url = (
            "https://wenxin.baidu.com/younger/portal/api/rest/1.0/ernievilg/v1/txt2img"
        )
        r = await self.request(url, data={"text": text, "style": style})
        if r["code"] == 0:
            logger.info(f'taskId: {r["data"]["taskId"]}')
            return r["data"]["taskId"]
        logger.info(f"获取taskId失败,返回msg: {r}")

    # 获取绘画的结果
    async def get_imgs(self, taskId):
        url = "https://wenxin.baidu.com/younger/portal/api/rest/1.0/ernievilg/v1/getImg"
        await asyncio.sleep(28)
        for _ in range(60):
            r = await self.request(url, data={"taskId": taskId})
            if r["code"] == 0:
                if r["data"]["imgUrls"]:  # 绘画完成
                    logger.info("绘画完成！")
                    return [img["image"] for img in r["data"]["imgUrls"]]
                else:
                    await asyncio.sleep(2)
            else:
                logger.info(f"绘画任务失败,返回msg: {r}")  # 请求失败的消息提示

    async def txt2imgs(self, text, style):
        taskId = await self.get_taskId(text, style)
        return await self.get_imgs(taskId)

    def match(self):  # 说 /wombo 则回复
        return self.on_command(["#wx"]) and self.uid in [1239504152, 2870471283]

    # 请求文心api,且在token失效时自动更新
    async def request(self, url, data):
        global vilg_token
        async with httpx.AsyncClient(verify=False, timeout=None) as client:
            data.update({"access_token": vilg_token[0]})
            r = (await client.post(url, data=data)).json()
            match r["code"]:
                case 0:
                    return r
                case 111:
                    logger.warning("token已失效，正在获取token……")
                    vilg_token = (await self.get_token(), 0)
                    data.update({"access_token": vilg_token[0]})
                    r = (await client.post(url, data=data)).json()
                case 1:
                    await self.send_msg(r["msg"])
                    raise Exception(r["msg"])

    async def handle(self):
        if len(self.args) <= 2:
            return await self.send_msg(
                "基于文心ERNIE-ViLG大模型，根据用户输入的文本，自动创作\n当前支持油画、水彩、卡通、粉笔画、儿童画、蜡笔画\n主要擅长风景写意画，请尽量给定比较明确的意象描述\n如: #wx 油画 江上落日与晚霞"
            )
        else:
            start_time = time.time()
            global vilg_token
            if (vilg_token := self.db.get("wx:access_token")) is None:
                self.db.update(
                    "wx:access_token", vilg_token := (await self.get_token(), 1)
                )
            if self.args[1] in style_list:
                text = " ".join(self.args[2:])
                style = self.args[1]
            else:
                text = " ".join(self.args[1:])
                style = choice(style_list)
            await self.send_msg(f"任务已创建，请耐心等待……")
            img_urls = await self.txt2imgs(text, style)
            msg_list = [
                Message.at(self.uid),
                Message.text(
                    f" 风格: {style}\n描述: {text}\n生成用时: {time.time()-start_time:.2f}s\n"
                ),
            ]
            msg_list.extend([Message.image(url) for url in img_urls])
            if vilg_token[1] == 0:
                self.db.update("wx:access_token", (vilg_token[0], 1))
            logger.info("\n".join(img_urls))
            return await self.send_msg(*msg_list)
