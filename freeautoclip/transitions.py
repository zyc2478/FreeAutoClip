#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
转场效果模块 - 支持多种视频转场效果
"""

import cv2
import numpy as np
from .utils import VideoFileClip, CompositeVideoClip, concatenate_videoclips, VideoClip
from typing import List, Tuple, Optional, Callable
import os

from .config import TRANSITION_CONFIG, TEMP_DIR


class TransitionManager:
    """转场管理器"""
    
    def __init__(self):
        self.config = TRANSITION_CONFIG
        self.transitions = {
            "fade": self._fade_transition,
            "dissolve": self._dissolve_transition,
            "wipe_left": self._wipe_left_transition,
            "wipe_right": self._wipe_right_transition,
            "slide_left": self._slide_left_transition,
            "slide_right": self._slide_right_transition,
            "zoom_in": self._zoom_in_transition,
            "zoom_out": self._zoom_out_transition,
            "flip": self._flip_transition,
            "rotate": self._rotate_transition,
            "blur": self._blur_transition,
            "pixelate": self._pixelate_transition,
        }
    
    def get_available_transitions(self) -> List[str]:
        """获取可用的转场效果列表"""
        return list(self.transitions.keys())
    
    def apply_transition(self, clip1: VideoFileClip, 
                        clip2: VideoFileClip,
                        transition_type: str = "fade",
                        duration: float = None) -> VideoFileClip:
        """
        在两个视频片段之间应用转场效果
        
        Args:
            clip1: 第一个视频片段
            clip2: 第二个视频片段
            transition_type: 转场类型
            duration: 转场时长
            
        Returns:
            合并后的视频片段
        """
        if duration is None:
            duration = self.config["default_duration"]
        
        if transition_type not in self.transitions:
            raise ValueError(f"未知的转场类型: {transition_type}")
        
        transition_func = self.transitions[transition_type]
        return transition_func(clip1, clip2, duration)
    
    def _fade_transition(self, clip1: VideoFileClip, 
                        clip2: VideoFileClip,
                        duration: float) -> VideoFileClip:
        """淡入淡出转场"""
        # 创建交叉淡入淡出
        clip1_fade = clip1.fadeout(duration)
        clip2_fade = clip2.fadein(duration)
        
        # 合并
        return concatenate_videoclips([clip1_fade, clip2_fade], method="compose")
    
    def _dissolve_transition(self, clip1: VideoFileClip,
                            clip2: VideoFileClip,
                            duration: float) -> VideoFileClip:
        """溶解转场"""
        # 提取转场部分的帧
        fps = clip1.fps
        transition_frames = int(duration * fps)
        
        # 获取最后和开始的帧
        clip1_end = clip1.subclipped(max(0, clip1.duration - duration), clip1.duration)
        clip2_start = clip2.subclipped(0, min(duration, clip2.duration))
        
        # 创建溶解效果
        def make_frame(t):
            # 计算混合比例
            alpha = t / duration
            
            # 获取帧
            frame1 = clip1_end.get_frame(t)
            frame2 = clip2_start.get_frame(t)
            
            # 混合
            blended = cv2.addWeighted(frame1, 1 - alpha, frame2, alpha, 0)
            return blended
        
        # 创建转场片段
        # VideoClip already imported from utils
        transition_clip = VideoClip(make_frame, duration=duration)
        transition_clip = transition_clip.with_fps(fps)
        
        # 合并
        final = concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition_clip,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
        
        return final
    
    def _wipe_left_transition(self, clip1: VideoFileClip,
                             clip2: VideoFileClip,
                             duration: float) -> VideoFileClip:
        """向左擦除转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            wipe_point = int(w * progress)
            
            result = frame1.copy()
            if wipe_point < w:
                result[:, :wipe_point] = frame2[:, :wipe_point]
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _wipe_right_transition(self, clip1: VideoFileClip,
                              clip2: VideoFileClip,
                              duration: float) -> VideoFileClip:
        """向右擦除转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            wipe_point = int(w * (1 - progress))
            
            result = frame1.copy()
            if wipe_point > 0:
                result[:, wipe_point:] = frame2[:, wipe_point:]
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _slide_left_transition(self, clip1: VideoFileClip,
                              clip2: VideoFileClip,
                              duration: float) -> VideoFileClip:
        """向左滑动转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            offset = int(w * progress)
            
            result = np.zeros_like(frame1)
            
            # 第一个视频向右滑出
            if offset < w:
                result[:, :w-offset] = frame1[:, offset:]
            
            # 第二个视频从左边滑入
            if offset > 0:
                result[:, w-offset:] = frame2[:, :offset]
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _slide_right_transition(self, clip1: VideoFileClip,
                               clip2: VideoFileClip,
                               duration: float) -> VideoFileClip:
        """向右滑动转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            offset = int(w * progress)
            
            result = np.zeros_like(frame1)
            
            # 第一个视频向左滑出
            if offset < w:
                result[:, offset:] = frame1[:, :w-offset]
            
            # 第二个视频从右边滑入
            if offset > 0:
                result[:, :offset] = frame2[:, w-offset:]
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _zoom_in_transition(self, clip1: VideoFileClip,
                           clip2: VideoFileClip,
                           duration: float) -> VideoFileClip:
        """放大转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            
            # 第一个视频放大淡出
            scale1 = 1 + progress * 0.5
            new_h1, new_w1 = int(h * scale1), int(w * scale1)
            frame1_resized = cv2.resize(frame1, (new_w1, new_h1))
            
            y1 = (new_h1 - h) // 2
            x1 = (new_w1 - w) // 2
            frame1_cropped = frame1_resized[y1:y1+h, x1:x1+w]
            
            # 混合
            alpha = progress
            result = cv2.addWeighted(frame1_cropped, 1 - alpha, frame2, alpha, 0)
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _zoom_out_transition(self, clip1: VideoFileClip,
                            clip2: VideoFileClip,
                            duration: float) -> VideoFileClip:
        """缩小转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            
            # 第二个视频缩小淡入
            scale2 = 1.5 - progress * 0.5
            new_h2, new_w2 = int(h * scale2), int(w * scale2)
            frame2_resized = cv2.resize(frame2, (new_w2, new_h2))
            
            y2 = (new_h2 - h) // 2
            x2 = (new_w2 - w) // 2
            frame2_cropped = frame2_resized[y2:y2+h, x2:x2+w]
            
            # 混合
            alpha = progress
            result = cv2.addWeighted(frame1, 1 - alpha, frame2_cropped, alpha, 0)
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _flip_transition(self, clip1: VideoFileClip,
                        clip2: VideoFileClip,
                        duration: float) -> VideoFileClip:
        """翻转转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            
            # 3D翻转效果
            angle = progress * 90
            
            if progress < 0.5:
                # 前半段：翻转第一个视频
                scale = np.cos(np.radians(angle * 2))
                if scale > 0:
                    M = cv2.getRotationMatrix2D((w/2, h/2), 0, scale)
                    result = cv2.warpAffine(frame1, M, (w, h))
                else:
                    result = frame1
            else:
                # 后半段：翻转第二个视频
                scale = np.cos(np.radians((1 - progress) * 2 * 90))
                if scale > 0:
                    M = cv2.getRotationMatrix2D((w/2, h/2), 0, scale)
                    result = cv2.warpAffine(frame2, M, (w, h))
                else:
                    result = frame2
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _rotate_transition(self, clip1: VideoFileClip,
                          clip2: VideoFileClip,
                          duration: float) -> VideoFileClip:
        """旋转转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            
            # 旋转效果
            if progress < 0.5:
                angle = progress * 2 * 180
                M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1 - progress * 2)
                result = cv2.warpAffine(frame1, M, (w, h))
            else:
                angle = (progress - 0.5) * 2 * 180
                M = cv2.getRotationMatrix2D((w/2, h/2), angle - 180, (progress - 0.5) * 2)
                result = cv2.warpAffine(frame2, M, (w, h))
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _blur_transition(self, clip1: VideoFileClip,
                        clip2: VideoFileClip,
                        duration: float) -> VideoFileClip:
        """模糊转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            # 动态模糊
            if progress < 0.5:
                # 增加模糊
                blur_amount = int(progress * 2 * 20) * 2 + 1
                blurred = cv2.GaussianBlur(frame1, (blur_amount, blur_amount), 0)
                alpha = progress * 2
                result = cv2.addWeighted(frame1, 1 - alpha, blurred, alpha, 0)
            else:
                # 减少模糊
                blur_amount = int((1 - progress) * 2 * 20) * 2 + 1
                blurred = cv2.GaussianBlur(frame2, (blur_amount, blur_amount), 0)
                alpha = (progress - 0.5) * 2
                result = cv2.addWeighted(blurred, 1 - alpha, frame2, alpha, 0)
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def _pixelate_transition(self, clip1: VideoFileClip,
                            clip2: VideoFileClip,
                            duration: float) -> VideoFileClip:
        """像素化转场"""
        def make_frame(t):
            progress = t / duration
            
            frame1 = clip1.get_frame(min(t, clip1.duration - 0.001))
            frame2 = clip2.get_frame(min(t, clip2.duration - 0.001))
            
            h, w = frame1.shape[:2]
            
            # 像素化效果
            if progress < 0.5:
                # 增加像素化
                pixel_size = int(progress * 2 * 20) + 1
                small = cv2.resize(frame1, (w // pixel_size, h // pixel_size))
                pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
                alpha = progress * 2
                result = cv2.addWeighted(frame1, 1 - alpha, pixelated, alpha, 0)
            else:
                # 减少像素化
                pixel_size = int((1 - progress) * 2 * 20) + 1
                small = cv2.resize(frame2, (w // pixel_size, h // pixel_size))
                pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
                alpha = (progress - 0.5) * 2
                result = cv2.addWeighted(pixelated, 1 - alpha, frame2, alpha, 0)
            
            return result
        
        # VideoClip already imported from utils
        transition = VideoClip(make_frame, duration=duration)
        transition = transition.with_fps(clip1.fps)
        
        return concatenate_videoclips([
            clip1.subclipped(0, max(0, clip1.duration - duration)),
            transition,
            clip2.subclipped(min(duration, clip2.duration), clip2.duration)
        ])
    
    def auto_apply_transitions(self, clips: List[VideoFileClip],
                               transition_types: List[str] = None,
                               duration: float = None) -> VideoFileClip:
        """
        自动为多个片段应用转场效果
        
        Args:
            clips: 视频片段列表
            transition_types: 转场类型列表（循环使用）
            duration: 转场时长
            
        Returns:
            合并后的视频
        """
        if len(clips) < 2:
            return concatenate_videoclips(clips) if clips else None
        
        if transition_types is None:
            transition_types = self.get_available_transitions()
        
        if duration is None:
            duration = self.config["default_duration"]
        
        result = clips[0]
        
        for i, clip in enumerate(clips[1:], 1):
            transition_type = transition_types[(i - 1) % len(transition_types)]
            result = self.apply_transition(result, clip, transition_type, duration)
        
        return result
