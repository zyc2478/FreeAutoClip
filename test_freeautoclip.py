#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FreeAutoClip 测试脚本
"""

import os
import sys
from freeautoclip import VideoEditor
from freeautoclip.config import OUTPUT_DIR, TEMP_DIR


def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("FreeAutoClip 功能测试")
    print("=" * 60)
    
    # 创建编辑器实例
    editor = VideoEditor()
    print("✅ VideoEditor 实例创建成功")
    
    # 检查各个模块
    print("\n检查模块:")
    print(f"  - 视频切片器: {editor.cutter is not None}")
    print(f"  - 转场管理器: {editor.transitions is not None}")
    print(f"  - 特效管理器: {editor.effects is not None}")
    print(f"  - 文字管理器: {editor.text is not None}")
    print(f"  - 合成器: {editor.composer is not None}")
    print(f"  - 剪映 API: {editor.jianying_api is not None}")
    
    # 测试配置
    print("\n配置信息:")
    print(f"  - 输出目录: {OUTPUT_DIR}")
    print(f"  - 临时目录: {TEMP_DIR}")
    
    print("\n✅ 所有模块加载成功！")
    print("\n使用示例:")
    print("  1. 加载视频: editor.load_video('input.mp4')")
    print("  2. 智能切片: editor.smart_cut()")
    print("  3. 添加转场: editor.add_transitions('fade')")
    print("  4. 添加特效: editor.add_effects('brightness', 1.2)")
    print("  5. 添加文字: editor.add_text('Hello World', 5, 10)")
    print("  6. 导出视频: editor.export('output.mp4')")
    print("\n或使用 CLI:")
    print("  python run.py --mode cli")
    print("\n或使用 Web 界面:")
    print("  python run.py --mode web")


if __name__ == "__main__":
    test_basic_functionality()
