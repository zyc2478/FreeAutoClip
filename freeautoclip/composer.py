#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频合成模块 - 支持多轨道合成和音频混合
"""

import cv2
import numpy as np
from .utils import (VideoFileClip, AudioFileClip, CompositeVideoClip,
                           concatenate_videoclips, CompositeAudioClip, ColorClip)
try:
    from moviepy.audio.fx.all import audio_fadein, audio_fadeout
except ImportError:
    # MoviePy 2.x - 使用 with_effects 方法
    audio_fadein = None
    audio_fadeout = None
from typing import List, Tuple, Dict, Optional, Any
import os

from .config import VIDEO_CONFIG, AUDIO_CONFIG, OUTPUT_DIR, TEMP_DIR


class Track:
    """轨道类"""
    def __init__(self, name: str, track_type: str = "video"):
        self.name = name
        self.track_type = track_type  # video, audio, text
        self.clips: List[Dict[str, Any]] = []
        self.volume = 1.0
        self.muted = False
    
    def add_clip(self, clip, start_time: float = 0, 
                end_time: float = None,
                position: Tuple = ("center", "center")):
        """添加片段到轨道"""
        self.clips.append({
            "clip": clip,
            "start_time": start_time,
            "end_time": end_time,
            "position": position,
        })
    
    def remove_clip(self, index: int):
        """移除片段"""
        if 0 <= index < len(self.clips):
            del self.clips[index]
    
    def clear(self):
        """清空轨道"""
        self.clips = []


class VideoComposer:
    """视频合成器"""
    
    def __init__(self):
        self.config = VIDEO_CONFIG
        self.audio_config = AUDIO_CONFIG
        self.tracks: Dict[str, Track] = {}
        self.output_resolution = self.config["default_resolution"]
        self.output_fps = self.config["default_fps"]
        self.output_bitrate = self.config["default_bitrate"]
    
    def add_track(self, name: str, track_type: str = "video") -> Track:
        """添加轨道"""
        track = Track(name, track_type)
        self.tracks[name] = track
        return track
    
    def remove_track(self, name: str):
        """移除轨道"""
        if name in self.tracks:
            del self.tracks[name]
    
    def get_track(self, name: str) -> Optional[Track]:
        """获取轨道"""
        return self.tracks.get(name)
    
    def set_output_params(self, resolution: Tuple[int, int] = None,
                         fps: int = None,
                         bitrate: str = None):
        """设置输出参数"""
        if resolution:
            self.output_resolution = resolution
        if fps:
            self.output_fps = fps
        if bitrate:
            self.output_bitrate = bitrate
    
    def compose(self, output_path: str = None,
               duration: float = None,
               include_audio: bool = True) -> VideoFileClip:
        """
        合成视频
        
        Args:
            output_path: 输出路径
            duration: 输出时长（默认自动计算）
            include_audio: 是否包含音频
            
        Returns:
            合成后的视频片段
        """
        video_clips = []
        audio_clips = []
        
        # 处理视频轨道
        for track_name, track in self.tracks.items():
            if track.track_type == "video" and not track.muted:
                for clip_info in track.clips:
                    clip = clip_info["clip"]
                    start_time = clip_info["start_time"]
                    position = clip_info["position"]
                    
                    # 设置位置和开始时间
                    clip = clip.with_position(position)
                    clip = clip.with_start(start_time)
                    
                    # 调整分辨率
                    if clip.size != self.output_resolution:
                        clip = clip.resize(self.output_resolution)
                    
                    video_clips.append(clip)
            
            elif track.track_type == "audio" and not track.muted and include_audio:
                for clip_info in track.clips:
                    clip = clip_info["clip"]
                    start_time = clip_info["start_time"]
                    
                    # 调整音量
                    if track.volume != 1.0:
                        clip = clip.volumex(track.volume)
                    
                    clip = clip.with_start(start_time)
                    audio_clips.append(clip)
        
        # 合成视频
        if video_clips:
            final_video = CompositeVideoClip(video_clips, size=self.output_resolution)
        else:
            # 创建空白视频
            final_video = ColorClip(size=self.output_resolution, 
                                   color=(0, 0, 0), 
                                   duration=duration or 1)
        
        # 合成音频
        if audio_clips and include_audio:
            final_audio = CompositeAudioClip(audio_clips)
            final_video = final_video.with_audio(final_audio)
        
        # 设置时长
        if duration:
            final_video = final_video.with_duration(duration)
        
        # 导出
        if output_path:
            final_video.write_videofile(
                output_path,
                fps=self.output_fps,
                bitrate=self.output_bitrate,
                codec=self.config["default_codec"],
                audio_codec=self.config["audio_codec"],
                audio_bitrate=self.config["audio_bitrate"],
                verbose=False,
                logger=None
            )
        
        return final_video
    
    def merge_videos(self, video_paths: List[str],
                    output_path: str = None,
                    transitions: bool = False,
                    transition_duration: float = 0.5) -> VideoFileClip:
        """
        合并多个视频
        
        Args:
            video_paths: 视频路径列表
            output_path: 输出路径
            transitions: 是否添加转场
            transition_duration: 转场时长
            
        Returns:
            合并后的视频
        """
        clips = [VideoFileClip(path) for path in video_paths]
        
        if transitions:
            from .transitions import TransitionManager
            tm = TransitionManager()
            final = tm.auto_apply_transitions(clips, duration=transition_duration)
        else:
            final = concatenate_videoclips(clips, method="compose")
        
        if output_path:
            final.write_videofile(
                output_path,
                fps=self.output_fps,
                codec=self.config["default_codec"],
                audio_codec=self.config["audio_codec"],
                verbose=False,
                logger=None
            )
        
        return final
    
    def add_bgm(self, video: VideoFileClip,
               bgm_path: str,
               volume: float = None,
               fade_in: float = 1.0,
               fade_out: float = 1.0,
               loop: bool = True) -> VideoFileClip:
        """
        添加背景音乐
        
        Args:
            video: 视频片段
            bgm_path: 背景音乐路径
            volume: 音量
            fade_in: 淡入时长
            fade_out: 淡出时长
            loop: 是否循环
            
        Returns:
            处理后的视频
        """
        if volume is None:
            volume = self.audio_config["bgm_volume"]
        
        # 加载背景音乐
        bgm = AudioFileClip(bgm_path)
        
        # 循环背景音乐以匹配视频长度
        if loop and bgm.duration < video.duration:
            from moviepy.editor import concatenate_audioclips
            loops_needed = int(video.duration / bgm.duration) + 1
            bgm = concatenate_audioclips([bgm] * loops_needed)
        
        # 裁剪到视频长度
        bgm = bgm.subclipped(0, video.duration)
        
        # 应用淡入淡出
        if fade_in > 0 and audio_fadein:
            bgm = audio_fadein(bgm, fade_in)
        if fade_out > 0 and audio_fadeout:
            bgm = audio_fadeout(bgm, fade_out)
        
        # 调整音量
        bgm = bgm.volumex(volume)
        
        # 混合音频
        if video.audio is not None:
            final_audio = CompositeAudioClip([video.audio, bgm])
        else:
            final_audio = bgm
        
        return video.with_audio(final_audio)
    
    def add_voiceover(self, video: VideoFileClip,
                     voice_path: str,
                     start_time: float = 0,
                     volume: float = None) -> VideoFileClip:
        """
        添加配音
        
        Args:
            video: 视频片段
            voice_path: 配音文件路径
            start_time: 开始时间
            volume: 音量
            
        Returns:
            处理后的视频
        """
        if volume is None:
            volume = self.audio_config["voice_volume"]
        
        voice = AudioFileClip(voice_path)
        voice = voice.volumex(volume)
        voice = voice.with_start(start_time)
        
        if video.audio is not None:
            final_audio = CompositeAudioClip([video.audio, voice])
        else:
            final_audio = voice
        
        return video.with_audio(final_audio)
    
    def add_sound_effects(self, video: VideoFileClip,
                         effects: List[Dict[str, Any]]) -> VideoFileClip:
        """
        添加音效
        
        Args:
            video: 视频片段
            effects: 音效列表
                [
                    {
                        "path": "sound.mp3",
                        "start_time": 1.0,
                        "volume": 0.8
                    },
                    ...
                ]
            
        Returns:
            处理后的视频
        """
        audio_clips = []
        
        if video.audio is not None:
            audio_clips.append(video.audio)
        
        for effect in effects:
            sfx = AudioFileClip(effect["path"])
            sfx = sfx.volumex(effect.get("volume", 1.0))
            sfx = sfx.with_start(effect["start_time"])
            audio_clips.append(sfx)
        
        final_audio = CompositeAudioClip(audio_clips)
        return video.with_audio(final_audio)
    
    def picture_in_picture(self, main_video: VideoFileClip,
                          pip_video: VideoFileClip,
                          position: Tuple[str, str] = ("right", "bottom"),
                          size_ratio: float = 0.25,
                          margin: int = 20) -> CompositeVideoClip:
        """
        画中画效果
        
        Args:
            main_video: 主视频
            pip_video: 画中画视频
            position: 位置
            size_ratio: 大小比例
            margin: 边距
            
        Returns:
            合成后的视频
        """
        main_w, main_h = main_video.size
        
        # 计算画中画尺寸
        pip_w = int(main_w * size_ratio)
        pip_h = int(pip_w * pip_video.h / pip_video.w)
        
        # 调整画中画大小
        pip_video = pip_video.resize((pip_w, pip_h))
        
        # 计算位置
        h_pos, v_pos = position
        
        if h_pos == "left":
            x = margin
        elif h_pos == "center":
            x = (main_w - pip_w) // 2
        else:  # right
            x = main_w - pip_w - margin
        
        if v_pos == "top":
            y = margin
        elif v_pos == "center":
            y = (main_h - pip_h) // 2
        else:  # bottom
            y = main_h - pip_h - margin
        
        pip_video = pip_video.with_position((x, y))
        
        return CompositeVideoClip([main_video, pip_video])
    
    def split_screen(self, videos: List[VideoFileClip],
                    layout: str = "horizontal",
                    output_size: Tuple[int, int] = None) -> VideoFileClip:
        """
        分屏效果
        
        Args:
            videos: 视频列表
            layout: 布局方式（horizontal/vertical/grid）
            output_size: 输出尺寸
            
        Returns:
            合成后的视频
        """
        if output_size is None:
            output_size = self.output_resolution
        
        out_w, out_h = output_size
        n = len(videos)
        
        clips = []
        
        if layout == "horizontal":
            # 水平排列
            cell_w = out_w // n
            cell_h = out_h
            
            for i, video in enumerate(videos):
                # 调整大小并保持比例
                scale = min(cell_w / video.w, cell_h / video.h)
                new_w = int(video.w * scale)
                new_h = int(video.h * scale)
                video = video.resize((new_w, new_h))
                
                # 居中放置
                x = i * cell_w + (cell_w - new_w) // 2
                y = (cell_h - new_h) // 2
                
                video = video.with_position((x, y))
                clips.append(video)
        
        elif layout == "vertical":
            # 垂直排列
            cell_w = out_w
            cell_h = out_h // n
            
            for i, video in enumerate(videos):
                scale = min(cell_w / video.w, cell_h / video.h)
                new_w = int(video.w * scale)
                new_h = int(video.h * scale)
                video = video.resize((new_w, new_h))
                
                x = (cell_w - new_w) // 2
                y = i * cell_h + (cell_h - new_h) // 2
                
                video = video.with_position((x, y))
                clips.append(video)
        
        elif layout == "grid":
            # 网格排列
            cols = int(np.ceil(np.sqrt(n)))
            rows = int(np.ceil(n / cols))
            
            cell_w = out_w // cols
            cell_h = out_h // rows
            
            for i, video in enumerate(videos):
                row = i // cols
                col = i % cols
                
                scale = min(cell_w / video.w, cell_h / video.h)
                new_w = int(video.w * scale)
                new_h = int(video.h * scale)
                video = video.resize((new_w, new_h))
                
                x = col * cell_w + (cell_w - new_w) // 2
                y = row * cell_h + (cell_h - new_h) // 2
                
                video = video.with_position((x, y))
                clips.append(video)
        
        return CompositeVideoClip(clips, size=output_size)
    
    def chroma_key(self, video: VideoFileClip,
                  color: Tuple[int, int, int] = (0, 255, 0),
                  threshold: int = 100) -> VideoFileClip:
        """
        绿幕抠像
        
        Args:
            video: 视频片段
            color: 要抠除的颜色（默认绿色）
            threshold: 颜色阈值
            
        Returns:
            处理后的视频
        """
        def apply_chroma_key(frame):
            # 计算与目标颜色的距离
            diff = np.abs(frame.astype(np.float32) - np.array(color))
            distance = np.sqrt(np.sum(diff ** 2, axis=2))
            
            # 创建遮罩
            mask = distance > threshold
            
            # 应用遮罩
            result = frame.copy()
            alpha = np.expand_dims(mask.astype(np.uint8) * 255, axis=2)
            result = np.concatenate([result, alpha], axis=2)
            
            return result
        
        return video.fl_image(apply_chroma_key)
