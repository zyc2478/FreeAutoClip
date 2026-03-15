#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
核心模块 - 视频编辑器主类
整合所有功能，提供统一的剪辑接口
"""

import os
import json
from typing import List, Dict, Optional, Any, Tuple

from .utils import VideoFileClip, AudioFileClip
from .config import OUTPUT_DIR, TEMP_DIR, AI_CONFIG
from .cutter import VideoCutter, VideoSegment
from .transitions import TransitionManager
from .effects import EffectManager
from .composer import VideoComposer, Track
from .text import TextOverlayManager
from .api.jianying_api import JianYingAPI


class VideoEditor:
    """视频编辑器主类"""
    
    def __init__(self, use_jianying_api: bool = False):
        """
        初始化视频编辑器
        
        Args:
            use_jianying_api: 是否使用剪映API
        """
        self.cutter = VideoCutter()
        self.transitions = TransitionManager()
        self.effects = EffectManager()
        self.composer = VideoComposer()
        self.text = TextOverlayManager()
        
        self.jianying_api = None
        if use_jianying_api:
            self.jianying_api = JianYingAPI()
        
        self.segments: List[VideoSegment] = []
        self.clips: List[VideoFileClip] = []
        self.project_config: Dict[str, Any] = {}
        
    def load_video(self, video_path: str) -> VideoFileClip:
        """
        加载视频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频片段对象
        """
        clip = VideoFileClip(video_path)
        return clip
    
    def smart_cut(self, video_path: str,
                  remove_silence: bool = True,
                  detect_highlights: bool = True,
                  min_clip_duration: float = None) -> List[VideoSegment]:
        """
        智能切片
        
        Args:
            video_path: 视频路径
            remove_silence: 是否移除静音
            detect_highlights: 是否检测高光
            min_clip_duration: 最小片段时长
            
        Returns:
            视频片段列表
        """
        self.segments = self.cutter.smart_cut(
            video_path,
            remove_silence=remove_silence,
            detect_highlights=detect_highlights,
            min_clip_duration=min_clip_duration
        )
        return self.segments
    
    def cut_by_duration(self, video_path: str,
                       clip_duration: float = 5.0,
                       overlap: float = 0.0) -> List[VideoSegment]:
        """
        按固定时长切片
        
        Args:
            video_path: 视频路径
            clip_duration: 片段时长
            overlap: 重叠时长
            
        Returns:
            视频片段列表
        """
        self.segments = self.cutter.cut_by_duration(
            video_path, clip_duration, overlap
        )
        return self.segments
    
    def apply_transitions(self, transition_types: List[str] = None,
                         duration: float = None) -> 'VideoEditor':
        """
        应用转场效果
        
        Args:
            transition_types: 转场类型列表
            duration: 转场时长
            
        Returns:
            self，支持链式调用
        """
        if not self.clips:
            raise ValueError("请先加载视频片段")
        
        if len(self.clips) < 2:
            return self
        
        final_clip = self.transitions.auto_apply_transitions(
            self.clips, transition_types, duration
        )
        
        self.clips = [final_clip]
        return self
    
    def apply_effects(self, effects_chain: List[Dict[str, Any]]) -> 'VideoEditor':
        """
        应用特效链
        
        Args:
            effects_chain: 特效链配置
            
        Returns:
            self，支持链式调用
        """
        if not self.clips:
            raise ValueError("请先加载视频片段")
        
        self.clips = [
            self.effects.apply_chains(clip, effects_chain)
            for clip in self.clips
        ]
        return self
    
    def add_text(self, text: str,
                position: Tuple[str, str] = ("center", "bottom"),
                start_time: float = 0,
                duration: float = None,
                style: Dict[str, Any] = None) -> 'VideoEditor':
        """
        添加文字
        
        Args:
            text: 文字内容
            position: 位置
            start_time: 开始时间
            duration: 持续时间
            style: 样式配置
            
        Returns:
            self，支持链式调用
        """
        if not self.clips:
            raise ValueError("请先加载视频片段")
        
        if duration is None:
            duration = self.clips[0].duration
        
        video_size = self.clips[0].size
        
        text_clip = self.text.create_text_overlay(
            text=text,
            duration=duration,
            video_size=video_size,
            position=position,
            **(style or {})
        )
        
        text_clip = text_clip.with_start(start_time)
        
        # 合成
        from .utils import CompositeVideoClip
        final = CompositeVideoClip([self.clips[0], text_clip])
        self.clips[0] = final
        
        return self
    
    def add_subtitles(self, subtitles: List[Dict[str, Any]],
                     style: Dict[str, Any] = None) -> 'VideoEditor':
        """
        添加字幕
        
        Args:
            subtitles: 字幕列表
            style: 样式配置
            
        Returns:
            self，支持链式调用
        """
        if not self.clips:
            raise ValueError("请先加载视频片段")
        
        final = self.text.add_subtitles(self.clips[0], subtitles, style)
        self.clips[0] = final
        
        return self
    
    def add_bgm(self, bgm_path: str,
               volume: float = 0.3,
               fade_in: float = 1.0,
               fade_out: float = 1.0) -> 'VideoEditor':
        """
        添加背景音乐
        
        Args:
            bgm_path: 背景音乐路径
            volume: 音量
            fade_in: 淡入时长
            fade_out: 淡出时长
            
        Returns:
            self，支持链式调用
        """
        if not self.clips:
            raise ValueError("请先加载视频片段")
        
        self.clips[0] = self.composer.add_bgm(
            self.clips[0], bgm_path, volume, fade_in, fade_out
        )
        return self
    
    def export(self, output_path: str = None,
              resolution: Tuple[int, int] = None,
              fps: int = None,
              bitrate: str = None) -> str:
        """
        导出视频
        
        Args:
            output_path: 输出路径
            resolution: 输出分辨率
            fps: 输出帧率
            bitrate: 输出码率
            
        Returns:
            输出文件路径
        """
        if not self.clips:
            raise ValueError("没有可导出的视频")
        
        if output_path is None:
            output_path = os.path.join(OUTPUT_DIR, "output.mp4")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 设置输出参数
        if resolution:
            self.composer.set_output_params(resolution=resolution)
        if fps:
            self.composer.set_output_params(fps=fps)
        if bitrate:
            self.composer.set_output_params(bitrate=bitrate)
        
        # 导出
        final_clip = self.clips[0]
        
        final_clip.write_videofile(
            output_path,
            fps=fps or 30,
            codec='libx264',
            audio_codec='aac',
            logger=None
        )
        
        return output_path
    
    def auto_edit(self, video_path: str,
                  output_path: str = None,
                  style: str = "dynamic") -> str:
        """
        自动剪辑 - 一键完成所有剪辑工作
        
        Args:
            video_path: 输入视频路径
            output_path: 输出路径
            style: 剪辑风格（dynamic/calm/energetic）
            
        Returns:
            输出文件路径
        """
        print("🎬 开始自动剪辑...")
        
        # 1. 智能切片
        print("📦 智能切片中...")
        segments = self.smart_cut(video_path)
        print(f"   生成 {len(segments)} 个片段")
        
        # 2. 加载片段
        self.clips = []
        for segment in segments:
            clip = self.cutter.export_segment(
                segment,
                os.path.join(TEMP_DIR, f"clip_{segment.start:.2f}.mp4")
            )
            self.clips.append(VideoFileClip(clip))
        
        # 3. 应用转场
        print("✨ 添加转场效果...")
        if len(self.clips) > 1:
            final = self.transitions.auto_apply_transitions(self.clips)
            self.clips = [final]
        
        # 4. 根据风格应用特效
        print(f"🎨 应用 {style} 风格特效...")
        if style == "dynamic":
            effects = [
                {"type": "contrast", "params": {"factor": 1.1}},
                {"type": "saturation", "params": {"factor": 1.2}},
            ]
        elif style == "calm":
            effects = [
                {"type": "brightness", "params": {"factor": 0.95}},
                {"type": "contrast", "params": {"factor": 0.95}},
            ]
        else:  # energetic
            effects = [
                {"type": "contrast", "params": {"factor": 1.2}},
                {"type": "saturation", "params": {"factor": 1.3}},
            ]
        
        self.clips[0] = self.effects.apply_chains(self.clips[0], effects)
        
        # 5. 导出
        print("💾 导出视频...")
        result = self.export(output_path)
        
        print(f"✅ 完成！输出文件: {result}")
        return result
    
    def batch_process(self, video_paths: List[str],
                     output_dir: str = None,
                     preset: str = "default") -> List[str]:
        """
        批量处理视频
        
        Args:
            video_paths: 视频路径列表
            output_dir: 输出目录
            preset: 预设配置
            
        Returns:
            输出文件路径列表
        """
        if output_dir is None:
            output_dir = OUTPUT_DIR
        
        os.makedirs(output_dir, exist_ok=True)
        
        output_paths = []
        
        for i, video_path in enumerate(video_paths):
            print(f"\n处理视频 {i+1}/{len(video_paths)}: {video_path}")
            
            output_name = f"batch_{i:04d}.mp4"
            output_path = os.path.join(output_dir, output_name)
            
            try:
                result = self.auto_edit(video_path, output_path)
                output_paths.append(result)
            except Exception as e:
                print(f"处理失败: {e}")
                continue
        
        return output_paths
    
    def save_project(self, project_path: str):
        """
        保存项目配置
        
        Args:
            project_path: 项目文件路径
        """
        project_data = {
            "segments": [
                {
                    "start": s.start,
                    "end": s.end,
                    "type": s.segment_type,
                    "video_path": s.video_path
                }
                for s in self.segments
            ],
            "config": self.project_config
        }
        
        with open(project_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
    
    def load_project(self, project_path: str):
        """
        加载项目配置
        
        Args:
            project_path: 项目文件路径
        """
        with open(project_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        self.segments = [
            VideoSegment(
                start=s["start"],
                end=s["end"],
                video_path=s["video_path"],
                segment_type=s["type"]
            )
            for s in project_data.get("segments", [])
        ]
        
        self.project_config = project_data.get("config", {})
