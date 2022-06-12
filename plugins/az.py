# -*- encoding: utf-8 -*-
"""
@File    :   az.py
@Time    :   2021/11/12 13:40:15
@Author  :   Ayatale 
@Version :   1.0
@Contact :   ayatale@qq.com
@Github  :   https://github.com/Brx86/Voidaya
@Desc    :   啊这加密,在“啊”与“这”之间隐写文本内容（其实图片也可以,但只能在QQ解密）
"""


from . import logger
from voidaya import Method
from binascii import a2b_hex

all_map = [["\u200B", "\u200C", "\u200D", "\u202A"], ["l", "|", "I", "1"]]
az_prefix = ["啊", "这"]


def str_to_az(str_text, map_type=0):
    text_map = all_map[map_type]
    encode_text, hex_text = "", str_text.encode().hex()
    for hex_num in hex_text:
        a = int(hex_num, 16) // 4
        b = int(hex_num, 16) % 4
        encode_text += text_map[a]
        encode_text += text_map[b]
    if map_type == 0:
        return f"{az_prefix[0]}{encode_text}{az_prefix[1]}"
    return encode_text


def az_to_str(encode_text, map_type=0):
    text_map = all_map[map_type]
    hex_text = ""
    for n in range(len(encode_text) // 2 - 1 + map_type):
        a = text_map.index(encode_text[2 * n + 1 - map_type])
        b = text_map.index(encode_text[2 * n + 2 - map_type])
        hex_text += hex(4 * a + b)[-1]
    return a2b_hex(hex_text).decode()


class Plugin(Method):
    def match(self):  # 说 /az 则回复
        return self.on_command(["/az"])

    async def handle(self):
        msg = "用法:\n az -e <待加密文字>\n az -d <待解密文字>\n az -s <加密前后缀，长度为两个字符>"
        if len(self.args) < 3:
            return await self.send_msg(msg)
        # 加密解密
        try:
            match self.args[1]:
                case "-e":
                    msg = str_to_az(self.args[2])
                case "-d":
                    msg = f"解密结果:\n{az_to_str(self.args[2])}"
                case "-e1":
                    msg = str_to_az(self.args[2], map_type=1)
                case "-d1":
                    msg = f"解密结果:\n{az_to_str(self.args[2], map_type=1)}"
                case "--set" | "-s":
                    if len(self.args[2]) == 2:
                        global az_prefix
                        az_prefix = list(self.args[2])
                        msg = f"设置成功! 加密前缀为{az_prefix[0]} 后缀为{az_prefix[1]}"
                    else:
                        print(f"设置失败, 参数错误")
        except Exception as e:
            logger.error(repr(e))
            msg = "加密好像出了问题……但一定不是aya的问题!"
        return await self.send_msg(msg)
