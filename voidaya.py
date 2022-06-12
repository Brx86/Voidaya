#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   voidaya.py
@Time    :   2022/05/31 21:32:53
@Author  :   Ayatale 
@Version :   1.1
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   Ayabot v3, an asynchronous bot inspired by voidbot. 
"""


import re, time, json
import asyncio

from config import *
from collections import deque
from plugins import logger, plugin_list
from typing import Any, List, Optional, Tuple, Union
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import connect, WebSocketClientProtocol as WSClient


class Echo:
    def __init__(self):
        self.echo_num = 0
        self.echo_list = deque(maxlen=20)

    def get(self) -> Tuple[int, asyncio.Queue[Any]]:
        self.echo_num += 1
        q: asyncio.Queue = asyncio.Queue(maxsize=1)
        self.echo_list.append((self.echo_num, q))
        return self.echo_num, q

    async def match(self, context: dict):
        for obj in self.echo_list:
            if context["echo"] == obj[0]:
                await obj[1].put(context)


class Database:
    def __init__(self):
        self.data = {}
        self.limit = {}
        self.times = deque(maxlen=20)

    def get(self, key) -> Optional[Any]:
        return self.data.get(key)

    def update(self, key: str, value: Union[int, str], log=True):
        self.data[key] = value
        if log is True:
            logger.info(f"DB: {key}=>{value}")

    def check_limit(self, name: str, maxlen: int = 5, limit_time: int = 30) -> bool:
        now_time = time.time()
        if self.limit.get(name) is None:
            self.limit[name] = deque(maxlen=maxlen)
        elif (
            len(self.limit[name]) >= maxlen
            and now_time - self.limit[name][0] < limit_time
        ):
            return False
        self.limit[name].append(now_time)
        return True

    def check_times(self, keyword: str) -> bool:
        if keyword in self.times:
            return True
        self.times.append(keyword)
        return False


class Method:
    def __init__(self, ws: WSClient, db: Database, echo: Echo, context: dict):
        self.ws = ws
        self.db = db
        self.echo = echo
        self.context = context
        self.raw = context["raw_message"]
        self.uid = context.get("user_id")
        self.gid = context.get("group_id")
        self.mid = context.get("message_id")
        self.role = context["sender"].get("role")
        self.args = str.split(self.raw)
        self.stime = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(self.context["time"]),
        )
        self.name = context["sender"].get("card") or context["sender"]["nickname"]

    def limited(self, maxlen: int, limit_time: int) -> bool:
        return self.db.check_limit(f"msg:{self.gid}:{self.uid}", maxlen, limit_time)

    def is_message(self) -> bool:
        return self.context["post_type"] in ["message", "message_sent"]

    def on_full_match(self, keyword: str = "") -> bool:
        return self.is_message() and self.raw == keyword

    def on_reg_match(self, pattern: str = "") -> bool:
        return self.is_message() and bool(re.search(pattern, self.raw))

    def on_command(self, commands: List[str]) -> bool:
        if self.is_message():
            msg_cmd = self.raw.split(" ", 1)[0]
            for cmd in commands:
                if cmd == msg_cmd:
                    return True
        return False

    def only_to_me(self) -> bool:
        for nick in NICKNAME + [f"[CQ:at,qq={self.context['self_id']}]"]:
            if self.is_message() and nick in self.raw:
                self.raw = self.raw.replace(nick, "")
                return True
        return False

    def super_user(self) -> bool:
        return self.uid in SUPER_USER

    def admin_user(self) -> bool:
        return self.super_user() or self.role in ("admin", "owner")

    async def call_api(self, action: str, params: dict) -> Optional[dict]:
        echo_num, q = self.echo.get()
        data = json.dumps({"action": action, "params": params, "echo": echo_num})
        logger.info(f"发送调用 <- {action}: {echo_num}")
        # 发送请求并等待返回
        await self.ws.send(data)
        try:
            return await asyncio.wait_for(q.get(), timeout=10)
        except asyncio.TimeoutError:
            logger.warning(f"Echo {echo_num} 调用超时")
            return None

    async def send_msg(self, *message: Tuple[str | dict]) -> Optional[int]:
        # https://github.com/botuniverse/onebot-11/blob/master/api/public.md#send_msg-%E5%8F%91%E9%80%81%E6%B6%88%E6%81%AF
        if isinstance(message[0], str):
            message = [{"type": "text", "data": {"text": message[0]}}]
        if self.gid:
            return await self.send_group_msg(*message)
        return await self.send_private_msg(*message)

    async def send_private_msg(self, *message: Tuple[str | dict]) -> Optional[int]:
        # https://github.com/botuniverse/onebot-11/blob/master/api/public.md#send_private_msg-%E5%8F%91%E9%80%81%E7%A7%81%E8%81%8A%E6%B6%88%E6%81%AF
        params = {"user_id": self.uid, "message": message}
        ret = await self.call_api("send_private_msg", params)
        if ret and ret.get("status") == "ok":
            return ret["data"]["message_id"]
        return None

    async def send_group_msg(self, *message: Tuple[str | dict]) -> Optional[int]:
        # https://github.com/botuniverse/onebot-11/blob/master/api/public.md#send_group_msg-%E5%8F%91%E9%80%81%E7%BE%A4%E6%B6%88%E6%81%AF
        params = {"group_id": self.context["group_id"], "message": message}
        ret = await self.call_api("send_group_msg", params)
        if ret and ret.get("status") == "ok":
            return ret["data"]["message_id"]
        return None


async def plugin_pool(ws: WSClient, context: dict):
    # 遍历插件列表，执行匹配
    for plugin in plugin_list:
        p = plugin.Plugin(ws, db, echo, context)
        if p.match():
            logger.info(f"匹配命令 -> {context.get('raw_message')}")
            await p.handle()


async def on_message(ws: WSClient, message: Union[str, bytes]):
    # https://github.com/botuniverse/onebot-11/blob/master/event/README.md
    context = json.loads(message := str(message).strip())
    if e := context.get("echo"):
        logger.success(f"调用返回 -> {e}")
        # 响应报文通过队列传递给调用 API 的函数
        await echo.match(context)
    elif context.get("meta_event_type"):
        logger.success(f"心跳事件 -> {context.get('self_id')}")
    else:
        logger.info(f"收到事件 -> {context.get('message_type')}:{context.get('post_type')}")
        # 消息事件，检测插件
        await plugin_pool(ws, context)


async def ws_client(ws_server: str):
    # 建立 WebSocket 连接
    async with connect(ws_server) as ws:
        if "meta_event_type" in json.loads(await ws.recv()):
            logger.info(f"Connected to {ws_server}")
        async for message in ws:
            asyncio.create_task(on_message(ws, message))


if __name__ == "__main__":
    echo = Echo()
    db = Database()
    while True:
        try:
            asyncio.run(ws_client(WS_URL))
        except KeyboardInterrupt:
            logger.warning("Closing connection by user.")
            exit(0)
        except ConnectionClosedError:
            logger.warning("Connection closed, retrying in 5 seconds...")
            time.sleep(5)
            continue
        except ConnectionRefusedError:
            logger.warning(f"{WS_URL} refused connection, retrying in 10 seconds...")
            time.sleep(10)
            continue
        except Exception as e:
            logger.error(repr(e))
            logger.warning(f"Retrying in 10 seconds...")
            time.sleep(10)
            continue
