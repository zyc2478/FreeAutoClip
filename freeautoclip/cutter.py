#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频切片模块 - 支持智能场景检测和音频分析
"""

import cv2
import numpy as np
import wave
import struct
from .utils import VideoFileClip, AudioFileClip
from scenedetect import detect, ContentDetector, ThresholdDetector
from typing import List, Tuple, Dict, Optional
import os
import tempfile

from .config import CUTTER_CONFIG, TEMP_DIR


class VideoSegment:
    """视频片段类"""
    def __init__(self, start: float, end: float, video_path: str, 
                 segment_type: str = "normal", confidence: float = 1.0):
        self.start = start
        self.end = end
        self.duration = end - start
        self.video_path = video_path
        self.segment_type = segment_type  # normal, highlight, silence, scene_change
        self.confidence = confidence
        self.features = {}
    
    def __repr__(self):
        return f"VideoSegment({self.start:.2f}s - {self.end:.2f}s, type={self.segment_type})"


class VideoCutter:
    """视频切片器"""
    
    def __init__(self):
        self.config = CUTTER_CONFIG
        self.segments: List[VideoSegment] = []
        
    def detect_scenes(self, video_path: str, threshold: float = None) -> List[Tuple[float, float]]:
        """
        使用场景检测算法识别视频场景变化
        
        Args:
            video_path: 视频文件路径
            threshold: 检测阈值
            
        Returns:
            场景时间戳列表 [(start, end), ...]
        """
        if threshold is None:
            threshold = self.config["scene_threshold"]
        
        # 使用 PySceneDetect 进行场景检测
        scene_list = detect(video_path, ContentDetector(threshold=threshold))
        
        scenes = []
        for i, scene in enumerate(scene_list):
            start_time = scene[0].get_seconds()
            end_time = scene[1].get_seconds()
            scenes.append((start_time, end_time))
        
        return scenes
    
    def detect_silence(self, video_path: str, 
                       threshold: int = None,
                       min_duration: float = None) -> List[Tuple[float, float]]:
        """
        检测视频中的静音片段（简化版本，不依赖 librosa）
        
        Args:
            video_path: 视频文件路径
            threshold: 静音阈值（dB）
            min_duration: 最小静音时长
            
        Returns:
            静音时间段列表 [(start, end), ...]
        """
        if threshold is None:
            threshold = self.config["silence_threshold"]
        if min_duration is None:
            min_duration = self.config["min_silence_duration"]
        
        # 提取音频
        video = VideoFileClip(video_path)
        audio = video.audio
        
        # 保存临时音频文件
        temp_audio = os.path.join(TEMP_DIR, f"temp_audio_{os.getpid()}.wav")
        audio.write_audiofile(temp_audio, fps=16000, nbytes=2, codec='pcm_s16le', logger=None)
        
        # 读取音频数据
        silence_segments = []
        try:
            with wave.open(temp_audio, 'rb') as wav_file:
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                # 读取所有帧
                raw_data = wav_file.readframes(n_frames)
                
                # 转换为 numpy 数组
                if sample_width == 2:
                    fmt = f"{n_frames * n_channels}h"
                    data = struct.unpack(fmt, raw_data)
                    data = np.array(data, dtype=np.float32)
                else:
                    data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
                
                # 如果是立体声，转换为单声道
                if n_channels == 2:
                    data = data.reshape(-1, 2).mean(axis=1)
                
                # 计算音频能量（每 0.1 秒一个窗口）
                window_size = int(framerate * 0.1)  # 0.1秒窗口
                energies = []
                
                for i in range(0, len(data) - window_size, window_size):
                    window = data[i:i + window_size]
                    energy = np.sqrt(np.mean(window ** 2))
                    energies.append(energy)
                
                if len(energies) == 0:
                    return []
                
                # 转换为 dB
                max_energy = max(energies) if max(energies) else 1
                db_values = 20 * np.log10(np.array(energies) / max_energy + 1e-10)
                
                # 检测静音段
                is_silence = db_values < threshold
                
                start = None
                for i, silent in enumerate(is_silence):
                    time = i * 0.1  # 0.1秒一个点
                    
                    if silent and start is None:
                        start = time
                    elif not silent and start is not None:
                        duration = time - start
                        if duration >= min_duration:
                            silence_segments.append((start, time))
                        start = None
                
                # 处理最后一个静音段
                if start is not None:
                    time = len(is_silence) * 0.1
                    duration = time - start
                    if duration >= min_duration:
                        silence_segments.append((start, time))
        
        except Exception as e:
            print(f"静音检测出错: {e}")
        
        # 清理临时文件
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        video.close()
        
        return silence_segments
    
    def detect_highlights(self, video_path: str, 
                          top_percent: float = 0.2) -> List[Tuple[float, float]]:
        """
        检测视频中的高光片段（基于视觉运动）
        
        Args:
            video_path: 视频文件路径
            top_percent: 选择前百分之多少作为高光
            
        Returns:
            高光时间段列表
        """
        # 计算视频运动特征
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        frame_interval = int(fps * 0.5)  # 每0.5秒采样一帧
        
        motion_scores = []
        timestamps = []
        prev_frame = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # 计算帧间差分
                    diff = cv2.absdiff(gray, prev_frame)
                    motion_score = np.mean(diff)
                    motion_scores.append(motion_score)
                    timestamps.append(frame_count / fps)
                
                prev_frame = gray
            
            frame_count += 1
        
        cap.release()
        
        if len(motion_scores) == 0:
            return []
        
        # 归一化
        motion_scores = np.array(motion_scores)
        motion_normalized = (motion_scores - np.min(motion_scores)) / (np.max(motion_scores) - np.min(motion_scores) + 1e-8)
        
        # 选择高光片段
        threshold = np.percentile(motion_normalized, (1 - top_percent) * 100)
        highlight_indices = np.where(motion_normalized >= threshold)[0]
        
        # 合并连续的帧
        highlights = []
        if len(highlight_indices) > 0:
            start_idx = highlight_indices[0]
            prev_idx = highlight_indices[0]
            
            for idx in highlight_indices[1:]:
                if idx - prev_idx > 1:
                    start_time = timestamps[start_idx]
                    end_time = timestamps[prev_idx] + 0.5
                    highlights.append((start_time, end_time))
                    start_idx = idx
                prev_idx = idx
            
            # 添加最后一个片段
            start_time = timestamps[start_idx]
            end_time = timestamps[prev_idx] + 0.5
            highlights.append((start_time, end_time))
        
        return highlights
    
    def cut_by_duration(self, video_path: str, 
                        clip_duration: float = None,
                        overlap: float = 0.0) -> List[VideoSegment]:
        """
        按固定时长切片
        
        Args:
            video_path: 视频文件路径
            clip_duration: 每个片段的时长
            overlap: 片段重叠时长
            
        Returns:
            VideoSegment 列表
        """
        if clip_duration is None:
            clip_duration = self.config["default_clip_duration"]
        
        video = VideoFileClip(video_path)
        total_duration = video.duration
        
        segments = []
        start = 0
        
        while start < total_duration:
            end = min(start + clip_duration, total_duration)
            
            if end - start >= self.config["min_clip_duration"]:
                segment = VideoSegment(start, end, video_path, "normal")
                segments.append(segment)
            
            start += clip_duration - overlap
        
        video.close()
        
        return segments
    
    def smart_cut(self, video_path: str,
                  remove_silence: bool = True,
                  detect_highlights: bool = True,
                  min_clip_duration: float = None) -> List[VideoSegment]:
        """
        智能切片 - 综合场景检测、静音检测和高光检测
        
        Args:
            video_path: 视频文件路径
            remove_silence: 是否移除静音片段
            detect_highlights: 是否检测高光片段
            min_clip_duration: 最小片段时长
            
        Returns:
            VideoSegment 列表
        """
        if min_clip_duration is None:
            min_clip_duration = self.config["min_clip_duration"]
        
        # 1. 场景检测
        scenes = self.detect_scenes(video_path)
        
        # 2. 静音检测
        silence_segments = []
        if remove_silence:
            try:
                silence_segments = self.detect_silence(video_path)
            except Exception as e:
                print(f"静音检测失败: {e}")
        
        # 3. 高光检测
        highlights = []
        if detect_highlights:
            try:
                highlights = self.detect_highlights(video_path)
            except Exception as e:
                print(f"高光检测失败: {e}")
        
        # 4. 合并和过滤
        video = VideoFileClip(video_path)
        total_duration = video.duration
        video.close()
        
        # 创建时间线
        segments = []
        
        for scene_start, scene_end in scenes:
            # 检查是否与静音段重叠
            is_silence = False
            for silence_start, silence_end in silence_segments:
                overlap_start = max(scene_start, silence_start)
                overlap_end = min(scene_end, silence_end)
                if overlap_end - overlap_start > (scene_end - scene_start) * 0.5:
                    is_silence = True
                    break
            
            if is_silence and remove_silence:
                continue
            
            # 检查是否是高光片段
            is_highlight = False
            for highlight_start, highlight_end in highlights:
                overlap_start = max(scene_start, highlight_start)
                overlap_end = min(scene_end, highlight_end)
                if overlap_end - overlap_start > 0:
                    is_highlight = True
                    break
            
            segment_type = "highlight" if is_highlight else "normal"
            
            if scene_end - scene_start >= min_clip_duration:
                segment = VideoSegment(
                    scene_start, scene_end, video_path, 
                    segment_type=segment_type
                )
                segments.append(segment)
        
        self.segments = segments
        return segments
    
    def export_segment(self, segment: VideoSegment, 
                       output_path: str,
                       resolution: Tuple[int, int] = None) -> str:
        """
        导出单个片段
        
        Args:
            segment: 视频片段
            output_path: 输出路径
            resolution: 输出分辨率
            
        Returns:
            输出文件路径
        """
        video = VideoFileClip(segment.video_path)
        clip = video.subclipped(segment.start, segment.end)
        
        if resolution:
            clip = clip.resized(resolution)
        
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        clip.close()
        video.close()
        
        return output_path
    
    def batch_export(self, output_dir: str,
                     prefix: str = "clip",
                     resolution: Tuple[int, int] = None) -> List[str]:
        """
        批量导出所有片段
        
        Args:
            output_dir: 输出目录
            prefix: 文件名前缀
            resolution: 输出分辨率
            
        Returns:
            输出文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        output_paths = []
        for i, segment in enumerate(self.segments):
            output_path = os.path.join(output_dir, f"{prefix}_{i:04d}.mp4")
            self.export_segment(segment, output_path, resolution)
            output_paths.append(output_path)
        
        return output_paths
