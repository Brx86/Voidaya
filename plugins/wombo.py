# -*- encoding: utf-8 -*-
"""
@File    :   wombo.py
@Time    :   2022/06/21 23:48:54
@Author  :   Ayatale 
@Version :   1.0
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   Hello World
"""

from . import logger
from tools import Message
from voidaya import Method
from random import randint
import time, random, httpx, asyncio

# 26种生成风格的名称
style_dict = {
    1: "Synthwave",
    2: "Ukiyoe",
    3: "NoStyle",
    4: "Steampunk",
    5: "FantasyArt",
    6: "Vibrant",
    7: "HD",
    8: "Pastel",
    9: "Psychic",
    10: "DarkFantasy",
    11: "Mystical",
    12: "Festive",
    13: "Baroque",
    14: "Etching",
    15: "S.Dali",
    16: "Wuhtercuhler",
    17: "Provenance",
    18: "RoseGold",
    19: "Moonwalker",
    20: "Blacklight",
    21: "Psychedelic",
    22: "Ghibli",
    23: "Surreal",
    24: "Love",
    25: "Death",
    26: "Robots",
}

style_text = "风格列表:\n" + "\n".join([f"{k}: {v}" for k, v in style_dict.items()])


class Wombo:
    # wombo的api，以及丁真裁剪后的背景图base64
    API = "https://app.wombo.art/api"

    # 初始化类（因为有异步函数所以不能用__init__）
    @classmethod
    async def init(cls, client):
        self = Wombo()
        self.client = client
        self.auth = await self.identify()
        return self

    # 多次尝试调用api
    async def call_api(self, method, api_url, params=None, data=None, headers=None):
        for _ in range(5):
            r = await self.client.request(
                method,
                api_url,
                json=data,
                params=params,
                headers=headers,
            )
            if r.status_code == 200:
                return r
            print(
                f"{r.status_code}: Failed to {method} api {api_url} , try {_+1} times..."
            )
            await asyncio.sleep(1)
        return None

    # 获取最新的token
    async def identify(self):
        r = await self.call_api(
            "POST",
            "https://identitytoolkit.googleapis.com/v1/accounts:signUp",
            params={"key": "AIzaSyDCvp5MTJLUdtBYEKYWXJrlLzu1zuKM6Xw"},
        )
        token = r.json().get("idToken")
        if token:
            print(f"Identified: {token[:50]}...")
            self.client.headers.update({"Authorization": f"bearer {token}"})
            return time.time()
        return None

    # 创建一个空任务
    async def get_task(self):
        r = await self.call_api(
            "POST",
            f"{Wombo.API}/tasks",
            data={"premium": "false"},
        )
        task_id = r.json().get("id")
        print(f"Created task: {task_id}")
        return task_id

    # 填写参数，初始化任务
    async def start_task(self, task_id, keywords, style=None):
        if style == None:
            style = random.randint(1, 26)
        r = await self.call_api(
            "PUT",
            f"{Wombo.API}/tasks/{task_id}",
            data={
                "input_spec": {
                    "prompt": keywords,
                    "style": style,
                    "display_freq": 10,
                }
            },
        )
        return style_dict[style]

    # 轮询请求，检查任务是否完成
    async def query_task(self, task_id):
        await asyncio.sleep(5)
        for _ in range(50):
            r = await self.call_api("GET", f"{Wombo.API}/tasks/{task_id}")
            status = r.json().get("state")
            print(f"Querying task for {_+1} times...{status}")
            if status == "completed":
                break
            else:
                await asyncio.sleep(1)
        else:
            raise TimeoutError("WOMBO响应超时")
        r = await self.call_api("POST", f"{Wombo.API}/tradingcard/{task_id}")
        return r.text

    # 用于运行全部步骤
    async def run(self, keywords, style=None):
        self.keywords = keywords
        task_id = await self.get_task()
        style_name = await self.start_task(task_id, keywords, style)
        url = await self.query_task(task_id)
        print("Task finished!")
        if url:
            return style_name, url.strip('"')
        return style_name, None


async def download(url, fn):
    async with httpx.AsyncClient(timeout=10) as c:
        print(f"Downloading...")
        r = await c.get(url)
        if r.status_code == 200:
            with open(f"/tmp/{fn}.jpg", "wb") as f:
                f.write(r.content)
        else:
            logger.error(f"Download Error: {r.status_code}")


class Plugin(Method):
    def match(self):  # 说 /wombo 则回复
        return self.on_command(["/wombo"])

    async def handle(self):
        if len(self.args) == 1:
            return await self.send_msg(
                "Generate a random dream image, powered by Wombo.Art\nhttps://github.com/Brx86/DingZhen"
            )
        if len(self.args) > 1:
            fn = time.time()
            if self.args[1] == "-l":
                return await self.send_msg(style_text)
            elif self.args[1].isdecimal() and len(self.args) > 2:
                st = int(self.args[1])
                kw = " ".join(self.args[2:])
            else:
                st = randint(1, 26)
                kw = " ".join(self.args[1:])
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    w = await Wombo.init(client)
                    style_name, url = await w.run(kw, st)
                    if "https" in url:
                        await self.send_msg(f"Style: {style_name}\nURL:\n{url}")
                        logger.info(f"WOMBO URL: {url}")
                        await download(url, fn)
                        msg = Message.image(f"file:////tmp/{fn}.jpg")
                    else:
                        msg = "呜呜请求出错了"
            except Exception as e:
                logger.error(repr(e))
                msg = "呜呜请求超时了"
            return await self.send_msg(msg)
