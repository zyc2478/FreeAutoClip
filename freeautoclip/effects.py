#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
特效模块 - 支持多种视频特效
"""

import cv2
import numpy as np
from .utils import VideoFileClip, VideoClip
from typing import Tuple, List, Optional, Dict, Any
import os

from .config import EFFECTS_CONFIG, TEMP_DIR


class EffectManager:
    """特效管理器"""
    
    def __init__(self):
        self.config = EFFECTS_CONFIG
        self.effects = {}
    
    def apply_speed(self, clip: VideoFileClip, 
                   speed_factor: float) -> VideoFileClip:
        """
        调整视频速度
        
        Args:
            clip: 视频片段
            speed_factor: 速度倍数（0.5-2.0）
            
        Returns:
            处理后的视频片段
        """
        # 限制速度范围
        min_speed, max_speed = self.config["speed_range"]
        speed_factor = np.clip(speed_factor, min_speed, max_speed)
        
        return clip.fx(VideoFileClip.speedx, speed_factor)
    
    def apply_brightness(self, clip: VideoFileClip,
                        factor: float) -> VideoFileClip:
        """
        调整亮度
        
        Args:
            clip: 视频片段
            factor: 亮度倍数（0.5-1.5）
            
        Returns:
            处理后的视频片段
        """
        min_val, max_val = self.config["brightness_range"]
        factor = np.clip(factor, min_val, max_val)
        
        def adjust_brightness(frame):
            return np.clip(frame * factor, 0, 255).astype(np.uint8)
        
        return clip.fl_image(adjust_brightness)
    
    def apply_contrast(self, clip: VideoFileClip,
                      factor: float) -> VideoFileClip:
        """
        调整对比度
        
        Args:
            clip: 视频片段
            factor: 对比度倍数（0.5-1.5）
            
        Returns:
            处理后的视频片段
        """
        min_val, max_val = self.config["contrast_range"]
        factor = np.clip(factor, min_val, max_val)
        
        def adjust_contrast(frame):
            mean = np.mean(frame)
            return np.clip((frame - mean) * factor + mean, 0, 255).astype(np.uint8)
        
        return clip.fl_image(adjust_contrast)
    
    def apply_saturation(self, clip: VideoFileClip,
                        factor: float) -> VideoFileClip:
        """
        调整饱和度
        
        Args:
            clip: 视频片段
            factor: 饱和度倍数（0.0-2.0）
            
        Returns:
            处理后的视频片段
        """
        min_val, max_val = self.config["saturation_range"]
        factor = np.clip(factor, min_val, max_val)
        
        def adjust_saturation(frame):
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
            return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        
        return clip.fl_image(adjust_saturation)
    
    def apply_blur(self, clip: VideoFileClip,
                  kernel_size: int = 5) -> VideoFileClip:
        """
        应用模糊效果
        
        Args:
            clip: 视频片段
            kernel_size: 模糊核大小
            
        Returns:
            处理后的视频片段
        """
        min_val, max_val = self.config["blur_range"]
        kernel_size = int(np.clip(kernel_size, min_val, max_val))
        
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        def apply_blur_filter(frame):
            return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
        
        return clip.fl_image(apply_blur_filter)
    
    def apply_sharpen(self, clip: VideoFileClip,
                     intensity: float = 1.0) -> VideoFileClip:
        """
        应用锐化效果
        
        Args:
            clip: 视频片段
            intensity: 锐化强度
            
        Returns:
            处理后的视频片段
        """
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) * intensity
        
        def apply_sharpen_filter(frame):
            return cv2.filter2D(frame, -1, kernel)
        
        return clip.fl_image(apply_sharpen_filter)
    
    def apply_shake(self, clip: VideoFileClip,
                   intensity: int = None,
                   frequency: float = 10.0) -> VideoFileClip:
        """
        应用抖动效果
        
        Args:
            clip: 视频片段
            intensity: 抖动强度
            frequency: 抖动频率
            
        Returns:
            处理后的视频片段
        """
        if intensity is None:
            intensity = self.config["shake_intensity"]
        
        def apply_shake_effect(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            
            # 计算抖动偏移
            offset_x = int(np.sin(t * frequency * 2 * np.pi) * intensity)
            offset_y = int(np.cos(t * frequency * 2 * np.pi) * intensity)
            
            # 创建变换矩阵
            M = np.float32([[1, 0, offset_x], [0, 1, offset_y]])
            
            return cv2.warpAffine(frame, M, (w, h))
        
        return clip.fl(apply_shake_effect)
    
    def apply_zoom(self, clip: VideoFileClip,
                  zoom_factor: float = 1.2,
                  center: Tuple[float, float] = (0.5, 0.5)) -> VideoFileClip:
        """
        应用缩放效果
        
        Args:
            clip: 视频片段
            zoom_factor: 缩放倍数
            center: 缩放中心点（相对坐标 0-1）
            
        Returns:
            处理后的视频片段
        """
        def apply_zoom_effect(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            
            # 计算新的尺寸
            new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
            
            # 缩放
            resized = cv2.resize(frame, (new_w, new_h))
            
            # 计算裁剪区域
            center_x = int(new_w * center[0])
            center_y = int(new_h * center[1])
            
            x1 = max(0, center_x - w // 2)
            y1 = max(0, center_y - h // 2)
            x2 = min(new_w, x1 + w)
            y2 = min(new_h, y1 + h)
            
            # 调整起始点以确保尺寸正确
            if x2 - x1 < w:
                x1 = max(0, x2 - w)
            if y2 - y1 < h:
                y1 = max(0, y2 - h)
            
            return resized[y1:y2, x1:x2]
        
        return clip.fl(apply_zoom_effect)
    
    def apply_ken_burns(self, clip: VideoFileClip,
                       start_zoom: float = 1.0,
                       end_zoom: float = 1.3,
                       start_center: Tuple[float, float] = (0.5, 0.5),
                       end_center: Tuple[float, float] = (0.5, 0.5)) -> VideoFileClip:
        """
        应用 Ken Burns 效果（动态缩放和平移）
        
        Args:
            clip: 视频片段
            start_zoom: 起始缩放倍数
            end_zoom: 结束缩放倍数
            start_center: 起始中心点
            end_center: 结束中心点
            
        Returns:
            处理后的视频片段
        """
        def apply_ken_burns_effect(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            
            # 计算当前进度
            progress = t / clip.duration
            
            # 插值计算当前缩放和中心点
            current_zoom = start_zoom + (end_zoom - start_zoom) * progress
            current_center = (
                start_center[0] + (end_center[0] - start_center[0]) * progress,
                start_center[1] + (end_center[1] - start_center[1]) * progress
            )
            
            # 计算新的尺寸
            new_h, new_w = int(h * current_zoom), int(w * current_zoom)
            
            # 缩放
            resized = cv2.resize(frame, (new_w, new_h))
            
            # 计算裁剪区域
            center_x = int(new_w * current_center[0])
            center_y = int(new_h * current_center[1])
            
            x1 = max(0, center_x - w // 2)
            y1 = max(0, center_y - h // 2)
            x2 = min(new_w, x1 + w)
            y2 = min(new_h, y1 + h)
            
            if x2 - x1 < w:
                x1 = max(0, x2 - w)
            if y2 - y1 < h:
                y1 = max(0, y2 - h)
            
            return resized[y1:y2, x1:x2]
        
        return clip.fl(apply_ken_burns_effect)
    
    def apply_color_grading(self, clip: VideoFileClip,
                           lut_file: str = None,
                           warmth: float = 0.0,
                           tint: float = 0.0) -> VideoFileClip:
        """
        应用调色/色彩分级
        
        Args:
            clip: 视频片段
            lut_file: LUT 文件路径
            warmth: 暖色调调整（-1.0 到 1.0）
            tint: 色调调整（-1.0 到 1.0）
            
        Returns:
            处理后的视频片段
        """
        def apply_color_grading_effect(frame):
            result = frame.astype(np.float32)
            
            # 暖色调调整
            if warmth != 0:
                result[:, :, 0] += warmth * 30  # 红色通道
                result[:, :, 2] -= warmth * 20  # 蓝色通道
            
            # 色调调整
            if tint != 0:
                result[:, :, 1] += tint * 20  # 绿色通道
            
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return clip.fl_image(apply_color_grading_effect)
    
    def apply_vintage(self, clip: VideoFileClip,
                     intensity: float = 0.5) -> VideoFileClip:
        """
        应用复古效果
        
        Args:
            clip: 视频片段
            intensity: 效果强度
            
        Returns:
            处理后的视频片段
        """
        def apply_vintage_effect(frame):
            # 降低饱和度
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[:, :, 1] *= (1 - intensity * 0.5)
            
            # 添加棕褐色调
            result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
            
            # 添加暖色调
            result[:, :, 0] += intensity * 20  # 红色
            result[:, :, 1] += intensity * 10  # 绿色
            
            # 降低对比度
            mean = np.mean(result)
            result = (result - mean) * (1 - intensity * 0.2) + mean
            
            # 添加噪点
            noise = np.random.normal(0, intensity * 10, result.shape)
            result += noise
            
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return clip.fl_image(apply_vintage_effect)
    
    def apply_black_white(self, clip: VideoFileClip,
                         contrast: float = 1.0) -> VideoFileClip:
        """
        应用黑白效果
        
        Args:
            clip: 视频片段
            contrast: 对比度
            
        Returns:
            处理后的视频片段
        """
        def apply_bw_effect(frame):
            # 转换为灰度
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # 调整对比度
            gray = gray.astype(np.float32)
            mean = np.mean(gray)
            gray = (gray - mean) * contrast + mean
            gray = np.clip(gray, 0, 255).astype(np.uint8)
            
            # 转回 RGB
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        
        return clip.fl_image(apply_bw_effect)
    
    def apply_vignette(self, clip: VideoFileClip,
                      intensity: float = 0.5) -> VideoFileClip:
        """
        应用暗角效果
        
        Args:
            clip: 视频片段
            intensity: 效果强度
            
        Returns:
            处理后的视频片段
        """
        def apply_vignette_effect(frame):
            h, w = frame.shape[:2]
            
            # 创建渐变遮罩
            x = np.linspace(-1, 1, w)
            y = np.linspace(-1, 1, h)
            X, Y = np.meshgrid(x, y)
            
            R = np.sqrt(X**2 + Y**2)
            mask = 1 - np.clip(R * intensity, 0, 1)
            
            # 应用遮罩
            result = frame.astype(np.float32)
            for c in range(3):
                result[:, :, c] *= mask
            
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return clip.fl_image(apply_vignette_effect)
    
    def apply_mirror(self, clip: VideoFileClip,
                    direction: str = "horizontal") -> VideoFileClip:
        """
        应用镜像效果
        
        Args:
            clip: 视频片段
            direction: 镜像方向（horizontal/vertical）
            
        Returns:
            处理后的视频片段
        """
        def apply_mirror_effect(frame):
            if direction == "horizontal":
                return cv2.flip(frame, 1)
            else:
                return cv2.flip(frame, 0)
        
        return clip.fl_image(apply_mirror_effect)
    
    def apply_rotate(self, clip: VideoFileClip,
                    angle: float = 90) -> VideoFileClip:
        """
        应用旋转效果
        
        Args:
            clip: 视频片段
            angle: 旋转角度
            
        Returns:
            处理后的视频片段
        """
        def apply_rotate_effect(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            
            # 计算旋转矩阵
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            return cv2.warpAffine(frame, M, (w, h))
        
        return clip.fl(apply_rotate_effect)
    
    def apply_chains(self, clip: VideoFileClip,
                    effects_chain: List[Dict[str, Any]]) -> VideoFileClip:
        """
        应用特效链
        
        Args:
            clip: 视频片段
            effects_chain: 特效链配置列表
                [
                    {"type": "speed", "params": {"speed_factor": 1.5}},
                    {"type": "brightness", "params": {"factor": 1.2}},
                    ...
                ]
            
        Returns:
            处理后的视频片段
        """
        result = clip
        
        effect_methods = {
            "speed": self.apply_speed,
            "brightness": self.apply_brightness,
            "contrast": self.apply_contrast,
            "saturation": self.apply_saturation,
            "blur": self.apply_blur,
            "sharpen": self.apply_sharpen,
            "shake": self.apply_shake,
            "zoom": self.apply_zoom,
            "ken_burns": self.apply_ken_burns,
            "color_grading": self.apply_color_grading,
            "vintage": self.apply_vintage,
            "black_white": self.apply_black_white,
            "vignette": self.apply_vignette,
            "mirror": self.apply_mirror,
            "rotate": self.apply_rotate,
        }
        
        for effect_config in effects_chain:
            effect_type = effect_config.get("type")
            effect_params = effect_config.get("params", {})
            
            if effect_type in effect_methods:
                result = effect_methods[effect_type](result, **effect_params)
        
        return result
