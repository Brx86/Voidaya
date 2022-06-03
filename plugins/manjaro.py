# -*- encoding: utf-8 -*-
"""
@File    :   manjaro.py
@Time    :   2022/06/01 20:09:29
@Author  :   Ayatale 
@Version :   1.1
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   使用指定了配置路径的pacman查询manjaro包信息
@Warning :   用到了Match-Case, 所以仅支持python3.10及以上版本; 不支持模糊查询
"""


import re
from . import logger
from tools import aiorun
from voidaya import Method


desc = {
    "软件库": "仓库",
    "名字": "包名",
    "版本": "版本",
    "下载大小": "大小",
    "描述": "描述",
    "依赖于": "依赖",
    "维护者": "维护者",
    "得票": "得票",
    "URL": "上游",
    "打包者": "打包者",
    "编译日期": "编译日期",
    "AUR URL": "AUR链接",
    "首次提交": "首次提交",
    "最后修改": "最后修改",
}
desc_dep = {
    "依赖于": "依赖",
    "生成依赖": "构建依赖",
    "可选依赖": "可选依赖",
    "检查依赖": "检查依赖",
}


def safename(text):
    return re.sub(r"[^a-zA-Z0-9\+_.-]", "", text)


async def search(pkg, dep=False):
    msg = ""
    pkg = safename(pkg)
    cmd = f"pacmanjaro -Si {pkg}"
    result = await aiorun(cmd)
    if not result:
        return
    logger.warning(result)
    dic = desc_dep if dep else desc
    for k, v in dic.items():
        partten = re.compile(f"{k}(.*?): (.*?)\n")
        info = partten.findall(result)
        if info:
            msg += f"{v}: {info[0][1]}\n"
    return msg.strip()


class Plugin(Method):
    def match(self):  # 检测命令/ma, /manjaro
        return self.on_command(["/ma", "/manjaro"])

    async def handle(self):
        if len(self.args) < 2:
            return await self.send_msg(
                "用法:\n #ma <包名> 查询全部仓库\n #ma -d <包名> 显示依赖\n #ma -F <文件> 查询某一文件所在包"
            )
        match self.args[1]:
            case "-F":
                pkg = safename(self.args[2])
                result = await aiorun(f"pacmanjaro -Fq {pkg}")
                lines = result.splitlines()
                text = result if len(lines) <= 10 else "\n".join(lines[:10])
                msg = text if text else "未找到此文件"
            case "-d":
                result = await search(self.args[1], dep=True)
                msg = result if result else "请输入正确的包名"
            case _:
                result = await search(self.args[1])
                msg = result if result else "请输入正确的包名"
        return await self.send_msg(msg)
