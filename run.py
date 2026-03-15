#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FreeAutoClip 启动脚本
"""

import os
import sys
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from freeautoclip.web_interface import run_web
from freeautoclip.cli import main as cli_main


def setup_environment():
    """设置环境"""
    # 创建必要的目录
    dirs = ['output', 'temp', 'assets/fonts', 'assets/music', 'assets/effects']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    print("✅ 环境初始化完成")


def main():
    parser = argparse.ArgumentParser(
        description="FreeAutoClip - 自动化视频剪辑"
    )
    
    parser.add_argument(
        '--mode',
        choices=['web', 'cli'],
        default='web',
        help='运行模式 (web: Web界面, cli: 命令行)'
    )
    
    parser.add_argument('--host', default='0.0.0.0', help='Web服务主机')
    parser.add_argument('--port', type=int, default=5000, help='Web服务端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args, remaining = parser.parse_known_args()
    
    # 设置环境
    setup_environment()
    
    if args.mode == 'web':
        print(f"🌐 启动 Web 服务...")
        print(f"   地址: http://{args.host}:{args.port}")
        run_web(host=args.host, port=args.port, debug=args.debug)
    else:
        # 命令行模式
        sys.argv = [sys.argv[0]] + remaining
        cli_main()


if __name__ == '__main__':
    main()
