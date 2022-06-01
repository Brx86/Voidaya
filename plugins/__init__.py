import sys, time
from pathlib import Path
from loguru import logger
from config import LOG, LOG_LEVEL
from pkgutil import iter_modules
from importlib import import_module

# 使用pathlib获取当前路径
PATH = Path(sys.argv[0]).parent.absolute()

# 初始化日志
logger.remove()
logger.add(sys.stderr, colorize=True, format=LOG, level=LOG_LEVEL)
logger.add(PATH / "logs" / f"{time.strftime('%Y-%m-%d')}.log", enqueue=True)

# 加载插件
plugin_list = []
for _, plugin_file, _ in iter_modules(["plugins"]):
    logger.info(f"Loading plugin: {plugin_file}")
    plugin_list.append(import_module(f"plugins.{plugin_file}"))
del plugin_file
