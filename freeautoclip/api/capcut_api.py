#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CapCut API 集成模块
支持调用 CapCut 的自动化剪辑功能
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional, Any, Tuple

from ..config import OUTPUT_DIR, TEMP_DIR


class CapCutAPI:
    """CapCut API 客户端"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.getenv("CAPCUT_API_KEY", "")
        self.api_secret = api_secret or os.getenv("CAPCUT_API_SECRET", "")
        self.base_url = "https://api.capcut.com"
        self.timeout = 30
        self.max_retries = 3
        
        self.session_token = None
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key
        }
        
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"
        
        return headers
    
    def _make_request(self, method: str, endpoint: str,
                     data: Dict = None, params: Dict = None,
                     files: Dict = None) -> Dict:
        """发送 HTTP 请求"""
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
                else:
                    response = requests.request(
                        method, url, headers=headers,
                        json=data, timeout=self.timeout
                    )
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"API 请求失败: {str(e)}")
                time.sleep(2 ** attempt)
        
        return {}
    
    def create_project(self, name: str, 
                      aspect_ratio: str = "16:9") -> Optional[str]:
        """创建项目"""
        data = {
            "name": name,
            "aspect_ratio": aspect_ratio
        }
        
        try:
            response = self._make_request("POST", "/v1/projects", data=data)
            return response.get("project_id")
        except Exception as e:
            print(f"创建项目失败: {e}")
            return None
    
    def import_media(self, project_id: str, 
                    file_path: str) -> Optional[str]:
        """导入媒体文件"""
        try:
            with open(file_path, 'rb') as f:
                files = {"file": f}
                data = {"project_id": project_id}
                
                response = self._make_request(
                    "POST", "/v1/media/import",
                    data=data, files=files
                )
                return response.get("media_id")
        except Exception as e:
            print(f"导入媒体失败: {e}")
            return None
    
    def auto_edit(self, project_id: str,
                 style: str = "dynamic") -> Optional[str]:
        """自动剪辑"""
        data = {
            "project_id": project_id,
            "style": style,
            "auto_transitions": True,
            "auto_effects": True,
            "auto_bgm": True
        }
        
        try:
            response = self._make_request(
                "POST", "/v1/auto-edit", data=data
            )
            return response.get("edit_id")
        except Exception as e:
            print(f"自动剪辑失败: {e}")
            return None
    
    def export_video(self, project_id: str,
                    resolution: str = "1080p") -> Optional[str]:
        """导出视频"""
        data = {
            "project_id": project_id,
            "resolution": resolution,
            "format": "mp4"
        }
        
        try:
            response = self._make_request(
                "POST", "/v1/export", data=data
            )
            return response.get("export_id")
        except Exception as e:
            print(f"导出失败: {e}")
            return None
