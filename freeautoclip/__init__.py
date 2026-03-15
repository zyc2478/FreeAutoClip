#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FreeAutoClip - 自动化视频剪辑系统
支持：切片、转场、特效、合成、花字、无轨合一
"""

__version__ = "1.0.0"
__author__ = "FreeAutoClip Team"

from .core import VideoEditor
from .cutter import VideoCutter
from .transitions import TransitionManager
from .effects import EffectManager
from .composer import VideoComposer
from .text import TextOverlayManager
from .api.jianying_api import JianYingAPI

__all__ = [
    'VideoEditor',
    'VideoCutter',
    'TransitionManager',
    'EffectManager',
    'VideoComposer',
    'TextOverlayManager',
    'JianYingAPI',
]