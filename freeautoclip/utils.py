#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数和兼容性处理
"""

# MoviePy 兼容性导入
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        concatenate_videoclips, TextClip, ImageClip,
        VideoClip, ColorClip, CompositeAudioClip
    )
except ImportError:
    # MoviePy 2.x 版本
    from moviepy import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        concatenate_videoclips, TextClip, ImageClip,
        VideoClip, ColorClip, CompositeAudioClip
    )

# 淡入淡出兼容性函数
def fadeout(clip, duration):
    """淡出效果（MoviePy 2.x 兼容）"""
    # MoviePy 2.x 使用 with_effects
    try:
        from moviepy.video.fx.fadeout import fadeout as fx_fadeout
        return clip.with_effects([fx_fadeout(duration)])
    except ImportError:
        # 手动实现
        def make_frame(t):
            if t < clip.duration - duration:
                return clip.get_frame(t)
            else:
                alpha = (clip.duration - t) / duration
                frame = clip.get_frame(t)
                return (frame * alpha).astype(frame.dtype)
        return VideoClip(make_frame, duration=clip.duration).with_fps(clip.fps)

def fadein(clip, duration):
    """淡入效果（MoviePy 2.x 兼容）"""
    # MoviePy 2.x 使用 with_effects
    try:
        from moviepy.video.fx.fadein import fadein as fx_fadein
        return clip.with_effects([fx_fadein(duration)])
    except ImportError:
        # 手动实现
        def make_frame(t):
            if t > duration:
                return clip.get_frame(t)
            else:
                alpha = t / duration
                frame = clip.get_frame(t)
                return (frame * alpha).astype(frame.dtype)
        return VideoClip(make_frame, duration=clip.duration).with_fps(clip.fps)

# 为 VideoFileClip、VideoClip 和 CompositeVideoClip 添加方法
VideoFileClip.fadeout = fadeout
VideoFileClip.fadein = fadein
VideoClip.fadeout = fadeout
VideoClip.fadein = fadein
CompositeVideoClip.fadeout = fadeout
CompositeVideoClip.fadein = fadein

__all__ = [
    'VideoFileClip', 'AudioFileClip', 'CompositeVideoClip',
    'concatenate_videoclips', 'TextClip', 'ImageClip',
    'VideoClip', 'ColorClip', 'CompositeAudioClip'
]
