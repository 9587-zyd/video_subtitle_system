#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 关键：在所有导入之前先导入 torch 和 whisper
import torch
import whisper

import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

# 现在导入 PyQt5
from PyQt5.QtWidgets import QApplication

# 最后导入你的模块
from src.gui import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()