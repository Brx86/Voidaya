# -*- encoding: utf-8 -*-
"""
@File    :   tools.py
@Time    :   2022/06/01 10:55:12
@Author  :   Ayatale 
@Version :   1.1
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   常用的函数工具
@Warning :   部分工具的使用需要安装httpx等第三方库
"""

import asyncio
from plugins import logger
from typing import Union, Optional


class Message:
    # 定义消息类型
    @staticmethod
    def text(string: str) -> dict:
        # https://github.com/botuniverse/onebot-11/blob/master/message/segment.md#%E7%BA%AF%E6%96%87%E6%9C%AC
        return {"type": "text", "data": {"text": string}}

    @staticmethod
    def image(file: str, cache: bool = True) -> dict:
        # https://github.com/botuniverse/onebot-11/blob/master/message/segment.md#%E5%9B%BE%E7%89%87
        return {"type": "image", "data": {"file": file, "cache": cache}}

    @staticmethod
    def record(file: str, cache: bool = True) -> dict:
        # https://github.com/botuniverse/onebot-11/blob/master/message/segment.md#%E8%AF%AD%E9%9F%B3
        return {"type": "record", "data": {"file": file, "cache": cache}}

    @staticmethod
    def at(qq: int) -> dict:
        # https://github.com/botuniverse/onebot-11/blob/master/message/segment.md#%E6%9F%90%E4%BA%BA
        return {"type": "at", "data": {"qq": qq}}

    @staticmethod
    def music(data: str) -> dict:
        # https://github.com/botuniverse/onebot-11/blob/master/message/segment.md#%E9%9F%B3%E4%B9%90%E5%88%86%E4%BA%AB-
        return {"type": "music", "data": {"type": "qq", "id": data}}


async def aiorun(cmd: str, timeout: int = 20) -> Union[str, bool]:
    from asyncio.subprocess import PIPE

    proc = await asyncio.create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)
    logger.warning(f"Command: {cmd}")
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        stdout, stderr = await proc.communicate()
        logger.error(f"{cmd!r} killed after {timeout} seconds")
    if stdout:
        return stdout.decode().strip()
    if proc.returncode == 0:
        return True
    logger.error(f"{cmd!r} exited with {proc.returncode}")
    if stderr:
        logger.warning(f"[stderr]:\n{stderr.decode()}")
    return False


async def silicon(text: str, lang: str = "bash", rp: bool = False) -> Optional[str]:
    with open(f"/tmp/text", "w") as f:
        text = text.replace("'", "’").replace('"', "’") if rp else text
        textlist = text.splitlines()
        text = text if len(textlist) < 100 else "\n".join(textlist[:100])
        f.write(text + "......")
    cmd = f"silicon /tmp/text -o/tmp/text.png -l{lang} -fLXGWWenKaiMono -b#000000 --no-window-controls"
    if await aiorun(cmd):
        return "file:///tmp/text.png"
    return None


async def pastebin(text: str, api: int = 0, lang: str = "sh", timeout: int = 10) -> str:
    import httpx
    from io import BytesIO

    pastebin_api = [
        "https://fars.ee/?u=1",
        "https://api.inetech.fun/clip?return=preview",
    ]
    info = text if len(text) < 20 else f"{text[:20]}......"
    logger.warning(f"Pastebin: {info}")
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(pastebin_api[0], files={"c": BytesIO(text.encode())})
            if r.status_code == 200:
                return f"{r.text.strip()}/{lang}" if api == 0 else r.text.strip()
            return f"请求出错，状态码 {r.status_code}"
    except httpx.ConnectTimeout:
        return "请求超时，请稍后再试"
