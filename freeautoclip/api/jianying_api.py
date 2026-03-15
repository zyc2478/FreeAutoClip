#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
剪映 API 集成模块
支持调用剪映的自动化剪辑功能
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ..config import JIANYING_CONFIG, OUTPUT_DIR, TEMP_DIR


class JianYingAPI:
    """剪映 API 客户端"""
    
    def __init__(self, app_key: str = None, app_secret: str = None):
        self.config = JIANYING_CONFIG
        self.app_key = app_key or self.config["app_key"]
        self.app_secret = app_secret or self.config["app_secret"]
        self.base_url = self.config["api_endpoint"]
        self.timeout = self.config["timeout"]
        self.max_retries = self.config["max_retries"]
        
        self.access_token = None
        self.token_expires = 0
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.access_token and time.time() < self.token_expires:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Dict = None, params: Dict = None,
                     files: Dict = None) -> Dict:
        """
        发送 HTTP 请求
        
        Args:
            method: 请求方法
            endpoint: API 端点
            data: 请求数据
            params: URL 参数
            files: 上传文件
            
        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "GET":
                    response = requests.get(
                        url, headers=headers, params=params, 
                        timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    if files:
                        # 文件上传
                        headers.pop("Content-Type", None)
                        response = requests.post(
                            url, headers=headers, data=data,
                            files=files, timeout=self.timeout
                        )
                    else:
                        response = requests.post(
                            url, headers=headers, json=data,
                            timeout=self.timeout
                        )
                elif method.upper() == "PUT":
                    response = requests.put(
                        url, headers=headers, json=data,
                        timeout=self.timeout
                    )
                elif method.upper() == "DELETE":
                    response = requests.delete(
                        url, headers=headers, timeout=self.timeout
                    )
                else:
                    raise ValueError(f"不支持的 HTTP 方法: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"API 请求失败: {str(e)}")
                time.sleep(2 ** attempt)  # 指数退避
        
        return {}
    
    def authenticate(self) -> bool:
        """
        认证并获取访问令牌
        
        Returns:
            是否认证成功
        """
        try:
            data = {
                "app_key": self.app_key,
                "app_secret": self.app_secret,
                "grant_type": "client_credentials"
            }
            
            response = self._make_request("POST", "/oauth/token", data=data)
            
            if "access_token" in response:
                self.access_token = response["access_token"]
                expires_in = response.get("expires_in", 3600)
                self.token_expires = time.time() + expires_in - 300  # 提前5分钟过期
                return True
            
            return False
            
        except Exception as e:
            print(f"认证失败: {e}")
            return False
    
    def upload_media(self, file_path: str, 
                    media_type: str = "video") -> Optional[str]:
        """
        上传媒体文件
        
        Args:
            file_path: 文件路径
            media_type: 媒体类型（video/audio/image）
            
        Returns:
            媒体ID
        """
        try:
            with open(file_path, 'rb') as f:
                files = {
                    "file": (os.path.basename(file_path), f, 
                            f"{media_type}/{Path(file_path).suffix[1:]}")
                }
                
                data = {"media_type": media_type}
                
                response = self._make_request(
                    "POST", "/v1/media/upload", 
                    data=data, files=files
                )
                
                return response.get("media_id")
                
        except Exception as e:
            print(f"上传失败: {e}")
            return None
    
    def create_project(self, name: str, 
                      resolution: Tuple[int, int] = (1920, 1080),
                      fps: int = 30,
                      duration: float = 0) -> Optional[str]:
        """
        创建剪辑项目
        
        Args:
            name: 项目名称
            resolution: 分辨率
            fps: 帧率
            duration: 初始时长
            
        Returns:
            项目ID
        """
        data = {
            "name": name,
            "width": resolution[0],
            "height": resolution[1],
            "fps": fps,
            "duration": duration
        }
        
        try:
            response = self._make_request("POST", "/v1/projects", data=data)
            return response.get("project_id")
        except Exception as e:
            print(f"创建项目失败: {e}")
            return None
    
    def add_media_to_timeline(self, project_id: str, 
                             media_id: str,
                             track_index: int = 0,
                             start_time: float = 0,
                             end_time: float = None,
                             trim_start: float = 0,
                             trim_end: float = None) -> bool:
        """
        添加媒体到时间线
        
        Args:
            project_id: 项目ID
            media_id: 媒体ID
            track_index: 轨道索引
            start_time: 在时间线上的开始时间
            end_time: 在时间线上的结束时间
            trim_start: 裁剪开始时间
            trim_end: 裁剪结束时间
            
        Returns:
            是否成功
        """
        data = {
            "media_id": media_id,
            "track_index": track_index,
            "start_time": start_time,
            "trim_start": trim_start
        }
        
        if end_time is not None:
            data["end_time"] = end_time
        if trim_end is not None:
            data["trim_end"] = trim_end
        
        try:
            response = self._make_request(
                "POST", 
                f"/v1/projects/{project_id}/timeline/clips",
                data=data
            )
            return "clip_id" in response
        except Exception as e:
            print(f"添加到时间线失败: {e}")
            return False
    
    def add_transition(self, project_id: str,
                      clip1_id: str,
                      clip2_id: str,
                      transition_type: str = "fade",
                      duration: float = 0.5) -> bool:
        """
        添加转场效果
        
        Args:
            project_id: 项目ID
            clip1_id: 第一个片段ID
            clip2_id: 第二个片段ID
            transition_type: 转场类型
            duration: 转场时长
            
        Returns:
            是否成功
        """
        data = {
            "clip1_id": clip1_id,
            "clip2_id": clip2_id,
            "transition_type": transition_type,
            "duration": duration
        }
        
        try:
            response = self._make_request(
                "POST",
                f"/v1/projects/{project_id}/transitions",
                data=data
            )
            return "transition_id" in response
        except Exception as e:
            print(f"添加转场失败: {e}")
            return False
    
    def add_text(self, project_id: str,
                text: str,
                start_time: float,
                duration: float,
                position: Tuple[float, float] = (0.5, 0.5),
                style: Dict[str, Any] = None) -> Optional[str]:
        """
        添加文字
        
        Args:
            project_id: 项目ID
            text: 文字内容
            start_time: 开始时间
            duration: 持续时间
            position: 位置（相对坐标 0-1）
            style: 样式配置
            
        Returns:
            文字元素ID
        """
        data = {
            "text": text,
            "start_time": start_time,
            "duration": duration,
            "position": {"x": position[0], "y": position[1]}
        }
        
        if style:
            data["style"] = style
        
        try:
            response = self._make_request(
                "POST",
                f"/v1/projects/{project_id}/texts",
                data=data
            )
            return response.get("text_id")
        except Exception as e:
            print(f"添加文字失败: {e}")
            return None
    
    def add_effect(self, project_id: str,
                  clip_id: str,
                  effect_type: str,
                  params: Dict[str, Any] = None) -> bool:
        """
        添加特效
        
        Args:
            project_id: 项目ID
            clip_id: 片段ID
            effect_type: 特效类型
            params: 特效参数
            
        Returns:
            是否成功
        """
        data = {
            "clip_id": clip_id,
            "effect_type": effect_type
        }
        
        if params:
            data["params"] = params
        
        try:
            response = self._make_request(
                "POST",
                f"/v1/projects/{project_id}/effects",
                data=data
            )
            return "effect_id" in response
        except Exception as e:
            print(f"添加特效失败: {e}")
            return False
    
    def export_project(self, project_id: str,
                      output_format: str = "mp4",
                      resolution: Tuple[int, int] = None,
                      quality: str = "high") -> Optional[str]:
        """
        导出项目
        
        Args:
            project_id: 项目ID
            output_format: 输出格式
            resolution: 输出分辨率
            quality: 输出质量
            
        Returns:
            导出任务ID
        """
        data = {
            "format": output_format,
            "quality": quality
        }
        
        if resolution:
            data["resolution"] = {
                "width": resolution[0],
                "height": resolution[1]
            }
        
        try:
            response = self._make_request(
                "POST",
                f"/v1/projects/{project_id}/export",
                data=data
            )
            return response.get("export_id")
        except Exception as e:
            print(f"导出项目失败: {e}")
            return None
    
    def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """
        获取导出状态
        
        Args:
            export_id: 导出任务ID
            
        Returns:
            导出状态信息
        """
        try:
            return self._make_request(
                "GET",
                f"/v1/exports/{export_id}"
            )
        except Exception as e:
            print(f"获取导出状态失败: {e}")
            return {}
    
    def download_export(self, export_id: str, 
                       output_path: str = None) -> Optional[str]:
        """
        下载导出的视频
        
        Args:
            export_id: 导出任务ID
            output_path: 输出路径
            
        Returns:
            下载的文件路径
        """
        try:
            # 获取下载链接
            status = self.get_export_status(export_id)
            
            if status.get("status") != "completed":
                print("导出尚未完成")
                return None
            
            download_url = status.get("download_url")
            if not download_url:
                print("没有可用的下载链接")
                return None
            
            # 下载文件
            if output_path is None:
                output_path = os.path.join(
                    OUTPUT_DIR, 
                    f"jianying_export_{export_id}.mp4"
                )
            
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return output_path
            
        except Exception as e:
            print(f"下载失败: {e}")
            return None
    
    def auto_edit(self, media_files: List[str],
                 template: str = "auto",
                 output_name: str = "auto_edited") -> Optional[str]:
        """
        自动剪辑
        
        Args:
            media_files: 媒体文件列表
            template: 剪辑模板
            output_name: 输出名称
            
        Returns:
            导出文件路径
        """
        try:
            # 1. 创建项目
            project_id = self.create_project(output_name)
            if not project_id:
                return None
            
            # 2. 上传媒体文件
            media_ids = []
            for file_path in media_files:
                media_id = self.upload_media(file_path)
                if media_id:
                    media_ids.append(media_id)
            
            if not media_ids:
                print("没有成功上传的媒体文件")
                return None
            
            # 3. 添加到时间线
            current_time = 0
            clip_ids = []
            
            for media_id in media_ids:
                # 这里简化处理，实际需要获取 clip_id
                success = self.add_media_to_timeline(
                    project_id, media_id, 
                    start_time=current_time
                )
                if success:
                    current_time += 5  # 假设每个片段5秒
            
            # 4. 导出
            export_id = self.export_project(project_id)
            if not export_id:
                return None
            
            # 5. 等待导出完成
            while True:
                status = self.get_export_status(export_id)
                if status.get("status") == "completed":
                    break
                elif status.get("status") == "failed":
                    print("导出失败")
                    return None
                time.sleep(5)
            
            # 6. 下载
            return self.download_export(export_id)
            
        except Exception as e:
            print(f"自动剪辑失败: {e}")
            return None
    
    def apply_smart_cut(self, video_path: str,
                       highlight_threshold: float = 0.7) -> Optional[str]:
        """
        应用智能切片
        
        Args:
            video_path: 视频路径
            highlight_threshold: 高光检测阈值
            
        Returns:
            剪辑后的视频路径
        """
        try:
            # 上传视频
            media_id = self.upload_media(video_path)
            if not media_id:
                return None
            
            # 创建项目
            project_id = self.create_project("smart_cut")
            if not project_id:
                return None
            
            # 调用智能剪辑API
            data = {
                "media_id": media_id,
                "cut_type": "smart",
                "highlight_threshold": highlight_threshold
            }
            
            response = self._make_request(
                "POST",
                "/v1/smart-cut",
                data=data
            )
            
            cut_media_id = response.get("cut_media_id")
            if not cut_media_id:
                return None
            
            # 添加到项目
            self.add_media_to_timeline(project_id, cut_media_id)
            
            # 导出
            export_id = self.export_project(project_id)
            if export_id:
                # 等待并下载
                while True:
                    status = self.get_export_status(export_id)
                    if status.get("status") == "completed":
                        return self.download_export(export_id)
                    elif status.get("status") == "failed":
                        return None
                    time.sleep(5)
            
            return None
            
        except Exception as e:
            print(f"智能切片失败: {e}")
            return None
