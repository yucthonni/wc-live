#!/bin/bash
# wc-live 快捷命令
# 用法: wc list | wc <序号> | wc <saishi_id>
cd ~/Code/worldcup-live && source .venv/bin/activate && exec python3 wc-live "$@"
