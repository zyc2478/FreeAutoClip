#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件 - FreeAutoClip
"""

import os

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# 确保目录存在
for dir_path in [OUTPUT_DIR, TEMP_DIR, ASSETS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 视频配置
VIDEO_CONFIG = {
    "default_resolution": (1920, 1080),  # 默认分辨率
    "default_fps": 30,  # 默认帧率
    "default_bitrate": "8000k",  # 默认码率
    "default_codec": "libx264",  # 默认编码器
    "audio_codec": "aac",  # 音频编码器
    "audio_bitrate": "192k",  # 音频码率
}

# 切片配置
CUTTER_CONFIG = {
    "min_clip_duration": 1.0,  # 最小片段时长（秒）
    "max_clip_duration": 30.0,  # 最大片段时长（秒）
    "default_clip_duration": 5.0,  # 默认片段时长（秒）
    "scene_threshold": 0.3,  # 场景检测阈值
    "silence_threshold": -40,  # 静音检测阈值（dB）
    "min_silence_duration": 0.5,  # 最小静音时长（秒）
}

# 转场配置
TRANSITION_CONFIG = {
    "default_duration": 0.5,  # 默认转场时长（秒）
    "available_transitions": [
        "fade",  # 淡入淡出
        "dissolve",  # 溶解
        "wipe_left",  # 向左擦除
        "wipe_right",  # 向右擦除
        "slide_left",  # 向左滑动
        "slide_right",  # 向右滑动
        "zoom_in",  # 放大
        "zoom_out",  # 缩小
        "flip",  # 翻转
        "rotate",  # 旋转
        "blur",  # 模糊
        "pixelate",  # 像素化
    ],
}

# 特效配置
EFFECTS_CONFIG = {
    "speed_range": (0.5, 2.0),  # 速度调整范围
    "brightness_range": (0.5, 1.5),  # 亮度调整范围
    "contrast_range": (0.5, 1.5),  # 对比度调整范围
    "saturation_range": (0.0, 2.0),  # 饱和度调整范围
    "blur_range": (0, 10),  # 模糊程度范围
    "shake_intensity": 10,  # 抖动强度
    "zoom_levels": [1.0, 1.1, 1.2, 1.3],  # 缩放级别
}

# 花字配置
TEXT_CONFIG = {
    "fonts_dir": os.path.join(ASSETS_DIR, "fonts"),
    "default_font": "SourceHanSansCN-Bold.otf",
    "default_font_size": 60,
    "default_color": "#FFFFFF",
    "stroke_color": "#000000",
    "stroke_width": 2,
    "shadow_color": "#000000",
    "shadow_offset": (3, 3),
    "animation_types": [
        "fade_in",  # 淡入
        "typewriter",  # 打字机效果
        "bounce",  # 弹跳
        "slide_up",  # 上滑
        "slide_down",  # 下滑
        "scale",  # 缩放
        "rotate",  # 旋转
    ],
}

# 剪映API配置
JIANYING_CONFIG = {
    "api_endpoint": "https://api.jianying.com",
    "app_key": os.getenv("JIANYING_APP_KEY", ""),
    "app_secret": os.getenv("JIANYING_APP_SECRET", ""),
    "timeout": 30,
    "max_retries": 3,
}

# 音频配置
AUDIO_CONFIG = {
    "sample_rate": 44100,
    "channels": 2,
    "format": "s16",
    "bgm_volume": 0.3,  # 背景音乐音量
    "voice_volume": 1.0,  # 人声音量
}

# 智能剪辑配置
AI_CONFIG = {
    "auto_cut_silence": True,  # 自动剪掉静音
    "auto_add_transitions": True,  # 自动添加转场
    "auto_sync_bgm": True,  # 自动同步背景音乐
    "highlight_detection": True,  # 高光片段检测
    "emotion_analysis": False,  # 情感分析
}

# 输出格式配置
OUTPUT_FORMATS = {
    "mp4": {"codec": "libx264", "audio_codec": "aac"},
    "mov": {"codec": "libx264", "audio_codec": "aac"},
    "avi": {"codec": "libx264", "audio_codec": "mp3"},
    "mkv": {"codec": "libx264", "audio_codec": "aac"},
    "webm": {"codec": "libvpx-vp9", "audio_codec": "libopus"},
}
