#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
花字模块 - 支持动态文字效果和动画
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .utils import VideoFileClip, CompositeVideoClip, TextClip, ImageClip, VideoClip
from typing import Tuple, List, Optional, Dict, Any
import os

from .config import TEXT_CONFIG, TEMP_DIR


class TextOverlayManager:
    """文字叠加管理器"""
    
    def __init__(self):
        self.config = TEXT_CONFIG
        self.fonts_dir = self.config["fonts_dir"]
        os.makedirs(self.fonts_dir, exist_ok=True)
    
    def _get_font_path(self, font_name: str = None) -> str:
        """获取字体文件路径"""
        if font_name is None:
            font_name = self.config["default_font"]
        
        font_path = os.path.join(self.fonts_dir, font_name)
        
        # 如果字体不存在，使用系统默认字体
        if not os.path.exists(font_path):
            # 尝试常见的中文字体路径
            system_fonts = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux
                "C:/Windows/Fonts/simhei.ttf",  # Windows
            ]
            for sys_font in system_fonts:
                if os.path.exists(sys_font):
                    return sys_font
        
        return font_path
    
    def create_text_overlay(self, text: str,
                           duration: float,
                           video_size: Tuple[int, int] = (1920, 1080),
                           position: Tuple[str, str] = ("center", "bottom"),
                           font_size: int = None,
                           font_color: str = None,
                           stroke_color: str = None,
                           stroke_width: int = None,
                           bg_color: str = None,
                           bg_alpha: float = 0.5,
                           animation: str = None,
                           animation_duration: float = 0.5) -> ImageClip:
        """
        创建文字叠加层
        
        Args:
            text: 文字内容
            duration: 显示时长
            video_size: 视频尺寸
            position: 位置 (horizontal, vertical)
            font_size: 字体大小
            font_color: 字体颜色
            stroke_color: 描边颜色
            stroke_width: 描边宽度
            bg_color: 背景颜色
            bg_alpha: 背景透明度
            animation: 动画类型
            animation_duration: 动画时长
            
        Returns:
            文字片段
        """
        if font_size is None:
            font_size = self.config["default_font_size"]
        if font_color is None:
            font_color = self.config["default_color"]
        if stroke_color is None:
            stroke_color = self.config["stroke_color"]
        if stroke_width is None:
            stroke_width = self.config["stroke_width"]
        
        # 创建文字图像
        font_path = self._get_font_path()
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        
        # 计算文字尺寸
        dummy_img = Image.new('RGB', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        
        # 处理多行文字
        lines = text.split('\n')
        line_heights = []
        line_widths = []
        
        for line in lines:
            bbox = dummy_draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            line_widths.append(line_width)
            line_heights.append(line_height)
        
        max_width = max(line_widths) if line_widths else 100
        total_height = sum(line_heights) + (len(lines) - 1) * font_size // 4
        
        # 添加边距
        padding_x = font_size
        padding_y = font_size // 2
        
        img_width = max_width + padding_x * 2 + stroke_width * 2
        img_height = total_height + padding_y * 2 + stroke_width * 2
        
        # 创建图像
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 绘制背景
        if bg_color:
            bg_rgb = self._hex_to_rgb(bg_color)
            draw.rectangle([0, 0, img_width, img_height], 
                         fill=(*bg_rgb, int(255 * bg_alpha)))
        
        # 绘制文字（带描边）
        y_offset = padding_y
        font_rgb = self._hex_to_rgb(font_color)
        stroke_rgb = self._hex_to_rgb(stroke_color)
        
        for i, line in enumerate(lines):
            x = (img_width - line_widths[i]) // 2
            y = y_offset
            
            # 绘制描边
            if stroke_width > 0:
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y + dy), line, 
                                    font=font, fill=(*stroke_rgb, 255))
            
            # 绘制主文字
            draw.text((x, y), line, font=font, fill=(*font_rgb, 255))
            
            y_offset += line_heights[i] + font_size // 4
        
        # 转换为 numpy 数组
        img_array = np.array(img)
        
        # 创建 ImageClip
        text_clip = ImageClip(img_array, duration=duration, transparent=True)
        
        # 设置位置
        x_pos, y_pos = self._calculate_position(
            position, video_size, (img_width, img_height)
        )
        text_clip = text_clip.with_position((x_pos, y_pos))
        
        # 应用动画
        if animation:
            text_clip = self._apply_animation(
                text_clip, animation, animation_duration, duration
            )
        
        return text_clip
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """将十六进制颜色转换为 RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _calculate_position(self, position: Tuple[str, str],
                           video_size: Tuple[int, int],
                           text_size: Tuple[int, int]) -> Tuple[int, int]:
        """计算文字位置"""
        h_pos, v_pos = position
        video_w, video_h = video_size
        text_w, text_h = text_size
        
        # 水平位置
        if h_pos == "left":
            x = 50
        elif h_pos == "center":
            x = (video_w - text_w) // 2
        elif h_pos == "right":
            x = video_w - text_w - 50
        else:
            x = int(h_pos)
        
        # 垂直位置
        if v_pos == "top":
            y = 50
        elif v_pos == "center":
            y = (video_h - text_h) // 2
        elif v_pos == "bottom":
            y = video_h - text_h - 100
        else:
            y = int(v_pos)
        
        return (x, y)
    
    def _apply_animation(self, clip: ImageClip,
                        animation_type: str,
                        animation_duration: float,
                        total_duration: float) -> ImageClip:
        """应用文字动画"""
        
        if animation_type == "fade_in":
            return clip.fadein(animation_duration)
        
        elif animation_type == "typewriter":
            # 打字机效果
            def make_frame(t):
                progress = min(t / animation_duration, 1.0)
                frame = clip.get_frame(t)
                
                # 根据进度裁剪显示区域
                h, w = frame.shape[:2]
                visible_width = int(w * progress)
                
                result = np.zeros_like(frame)
                result[:, :visible_width] = frame[:, :visible_width]
                
                return result
            
            # VideoClip already imported from utils
            return VideoClip(make_frame, duration=total_duration).with_fps(clip.fps)
        
        elif animation_type == "bounce":
            # 弹跳效果
            def make_frame(t):
                frame = clip.get_frame(t)
                
                if t < animation_duration:
                    # 弹跳动画
                    progress = t / animation_duration
                    bounce = np.abs(np.sin(progress * np.pi * 2)) * (1 - progress)
                    offset_y = int(bounce * 50)
                    
                    h, w = frame.shape[:2]
                    result = np.zeros_like(frame)
                    if offset_y < h:
                        result[offset_y:, :] = frame[:h-offset_y, :]
                    return result
                
                return frame
            
            # VideoClip already imported from utils
            return VideoClip(make_frame, duration=total_duration).with_fps(clip.fps)
        
        elif animation_type == "slide_up":
            # 上滑效果
            def make_frame(t):
                frame = clip.get_frame(t)
                
                if t < animation_duration:
                    progress = t / animation_duration
                    h, w = frame.shape[:2]
                    offset_y = int((1 - progress) * h)
                    
                    result = np.zeros_like(frame)
                    if offset_y < h:
                        result[:h-offset_y, :] = frame[offset_y:, :]
                    return result
                
                return frame
            
            # VideoClip already imported from utils
            return VideoClip(make_frame, duration=total_duration).with_fps(clip.fps)
        
        elif animation_type == "slide_down":
            # 下滑效果
            def make_frame(t):
                frame = clip.get_frame(t)
                
                if t < animation_duration:
                    progress = t / animation_duration
                    h, w = frame.shape[:2]
                    offset_y = int((1 - progress) * h)
                    
                    result = np.zeros_like(frame)
                    if offset_y < h:
                        result[offset_y:, :] = frame[:h-offset_y, :]
                    return result
                
                return frame
            
            # VideoClip already imported from utils
            return VideoClip(make_frame, duration=total_duration).with_fps(clip.fps)
        
        elif animation_type == "scale":
            # 缩放效果
            def make_frame(t):
                frame = clip.get_frame(t)
                
                if t < animation_duration:
                    progress = t / animation_duration
                    scale = 0.5 + progress * 0.5
                    
                    h, w = frame.shape[:2]
                    new_h, new_w = int(h * scale), int(w * scale)
                    
                    resized = cv2.resize(frame, (new_w, new_h))
                    
                    # 居中放置
                    result = np.zeros_like(frame)
                    y1 = (h - new_h) // 2
                    x1 = (w - new_w) // 2
                    result[y1:y1+new_h, x1:x1+new_w] = resized
                    
                    return result
                
                return frame
            
            # VideoClip already imported from utils
            return VideoClip(make_frame, duration=total_duration).with_fps(clip.fps)
        
        elif animation_type == "rotate":
            # 旋转效果
            def make_frame(t):
                frame = clip.get_frame(t)
                
                if t < animation_duration:
                    progress = t / animation_duration
                    angle = (1 - progress) * 360
                    
                    h, w = frame.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, progress)
                    
                    return cv2.warpAffine(frame, M, (w, h))
                
                return frame
            
            # VideoClip already imported from utils
            return VideoClip(make_frame, duration=total_duration).with_fps(clip.fps)
        
        return clip
    
    def add_subtitles(self, video: VideoFileClip,
                     subtitles: List[Dict[str, Any]],
                     style: Dict[str, Any] = None) -> CompositeVideoClip:
        """
        添加字幕
        
        Args:
            video: 视频片段
            subtitles: 字幕列表
                [
                    {
                        "text": "字幕内容",
                        "start": 0.0,
                        "end": 3.0,
                        "position": ("center", "bottom"),
                    },
                    ...
                ]
            style: 字幕样式
            
        Returns:
            合成后的视频
        """
        if style is None:
            style = {}
        
        clips = [video]
        video_size = video.size
        
        for sub in subtitles:
            text_clip = self.create_text_overlay(
                text=sub["text"],
                duration=sub["end"] - sub["start"],
                video_size=video_size,
                position=sub.get("position", ("center", "bottom")),
                font_size=style.get("font_size"),
                font_color=style.get("font_color"),
                stroke_color=style.get("stroke_color"),
                stroke_width=style.get("stroke_width"),
                bg_color=style.get("bg_color"),
                bg_alpha=style.get("bg_alpha", 0.5),
                animation=sub.get("animation"),
                animation_duration=sub.get("animation_duration", 0.3)
            )
            
            text_clip = text_clip.with_start(sub["start"])
            clips.append(text_clip)
        
        return CompositeVideoClip(clips)
    
    def add_title_card(self, video: VideoFileClip,
                      title: str,
                      subtitle: str = None,
                      duration: float = 3.0,
                      style: Dict[str, Any] = None) -> CompositeVideoClip:
        """
        添加标题卡片
        
        Args:
            video: 视频片段
            title: 主标题
            subtitle: 副标题
            duration: 显示时长
            style: 样式配置
            
        Returns:
            合成后的视频
        """
        if style is None:
            style = {}
        
        video_size = video.size
        clips = [video]
        
        # 主标题
        title_clip = self.create_text_overlay(
            text=title,
            duration=duration,
            video_size=video_size,
            position=("center", "center"),
            font_size=style.get("title_font_size", 80),
            font_color=style.get("title_color", "#FFFFFF"),
            stroke_width=3,
            animation="scale",
            animation_duration=0.5
        )
        title_clip = title_clip.with_start(0)
        clips.append(title_clip)
        
        # 副标题
        if subtitle:
            subtitle_clip = self.create_text_overlay(
                text=subtitle,
                duration=duration,
                video_size=video_size,
                position=("center", 550),
                font_size=style.get("subtitle_font_size", 40),
                font_color=style.get("subtitle_color", "#CCCCCC"),
                animation="fade_in",
                animation_duration=0.5
            )
            subtitle_clip = subtitle_clip.with_start(0.3)
            clips.append(subtitle_clip)
        
        return CompositeVideoClip(clips)
    
    def add_credits(self, video: VideoFileClip,
                   credits: List[Dict[str, str]],
                   duration: float = 5.0,
                   scroll_speed: float = 50.0) -> CompositeVideoClip:
        """
        添加滚动字幕
        
        Args:
            video: 视频片段
            credits:  credits 列表
                [
                    {"role": "导演", "name": "张三"},
                    {"role": "编剧", "name": "李四"},
                    ...
                ]
            duration: 显示时长
            scroll_speed: 滚动速度（像素/秒）
            
        Returns:
            合成后的视频
        """
        video_w, video_h = video.size
        
        # 创建长图
        font_size = 40
        line_height = 60
        total_height = len(credits) * line_height + video_h
        
        img = Image.new('RGBA', (video_w, total_height), (0, 0, 0, 180))
        draw = ImageDraw.Draw(img)
        
        font_path = self._get_font_path()
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        
        # 绘制 credits
        y_offset = video_h // 2
        for credit in credits:
            text = f"{credit['role']}: {credit['name']}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (video_w - text_width) // 2
            
            draw.text((x, y_offset), text, font=font, fill=(255, 255, 255, 255))
            y_offset += line_height
        
        # 创建滚动动画
        img_array = np.array(img)
        credits_clip = ImageClip(img_array, duration=duration, transparent=True)
        
        def scroll(get_frame, t):
            frame = get_frame(t)
            offset_y = int(t * scroll_speed)
            
            h, w = frame.shape[:2]
            if offset_y + video_h <= h:
                return frame[offset_y:offset_y+video_h, :]
            else:
                return frame[h-video_h:h, :]
        
        # VideoClip already imported from utils
        credits_clip = VideoClip(
            lambda t: scroll(credits_clip.get_frame, t),
            duration=duration
        ).with_fps(video.fps)
        
        credits_clip = credits_clip.with_start(video.duration - duration)
        
        return CompositeVideoClip([video, credits_clip])
