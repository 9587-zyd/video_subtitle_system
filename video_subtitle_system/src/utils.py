"""
工具函数：日志、文件操作等
"""
import logging
import os

def setup_logger(name=__name__, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger

def ensure_dirs(dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)