#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web 界面 - FreeAutoClip Web UI
基于 Flask 的 Web 界面
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import threading

from .core import VideoEditor
from .config import OUTPUT_DIR, TEMP_DIR, VIDEO_CONFIG

# 创建 Flask 应用
app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB 最大上传文件
app.config['UPLOAD_FOLDER'] = TEMP_DIR

# 任务状态存储
tasks = {}
tasks_lock = threading.Lock()

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'mp3', 'wav', 'aac'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """首页"""
    return render_template('editor.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{unique_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'file_id': unique_id,
            'filename': filename,
            'filepath': filepath
        })
    
    return jsonify({'error': '不支持的文件类型'}), 400


@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """分析视频"""
    data = request.json
    video_path = data.get('video_path')
    
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': '视频文件不存在'}), 400
    
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        
        info = {
            'duration': clip.duration,
            'fps': clip.fps,
            'size': clip.size,
            'bitrate': getattr(clip, 'bitrate', 'unknown'),
        }
        
        clip.close()
        
        return jsonify({
            'success': True,
            'info': info
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/smart-cut', methods=['POST'])
def smart_cut():
    """智能切片"""
    data = request.json
    video_path = data.get('video_path')
    remove_silence = data.get('remove_silence', True)
    detect_highlights = data.get('detect_highlights', True)
    
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': '视频文件不存在'}), 400
    
    task_id = str(uuid.uuid4())
    
    def process():
        try:
            with tasks_lock:
                tasks[task_id] = {
                    'status': 'processing',
                    'progress': 0,
                    'message': '开始智能切片...'
                }
            
            editor = VideoEditor()
            
            with tasks_lock:
                tasks[task_id]['progress'] = 20
                tasks[task_id]['message'] = '检测场景...'
            
            segments = editor.smart_cut(
                video_path,
                remove_silence=remove_silence,
                detect_highlights=detect_highlights
            )
            
            with tasks_lock:
                tasks[task_id]['progress'] = 80
                tasks[task_id]['message'] = '导出片段...'
            
            # 导出片段信息
            segments_info = []
            for i, seg in enumerate(segments):
                seg_info = {
                    'index': i,
                    'start': seg.start,
                    'end': seg.end,
                    'duration': seg.duration,
                    'type': seg.segment_type
                }
                segments_info.append(seg_info)
            
            with tasks_lock:
                tasks[task_id] = {
                    'status': 'completed',
                    'progress': 100,
                    'message': '完成',
                    'segments': segments_info,
                    'segment_count': len(segments)
                }
        
        except Exception as e:
            with tasks_lock:
                tasks[task_id] = {
                    'status': 'error',
                    'message': str(e)
                }
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({
        'success': True,
        'task_id': task_id
    })


@app.route('/api/auto-edit', methods=['POST'])
def auto_edit():
    """自动剪辑"""
    data = request.json
    video_path = data.get('video_path')
    style = data.get('style', 'dynamic')
    
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': '视频文件不存在'}), 400
    
    task_id = str(uuid.uuid4())
    output_filename = f"edited_{task_id[:8]}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    def process():
        try:
            with tasks_lock:
                tasks[task_id] = {
                    'status': 'processing',
                    'progress': 0,
                    'message': '开始自动剪辑...'
                }
            
            editor = VideoEditor()
            
            with tasks_lock:
                tasks[task_id]['progress'] = 10
                tasks[task_id]['message'] = '智能切片...'
            
            # 执行自动剪辑
            result = editor.auto_edit(video_path, output_path, style)
            
            with tasks_lock:
                tasks[task_id] = {
                    'status': 'completed',
                    'progress': 100,
                    'message': '完成',
                    'output_path': result,
                    'output_url': f'/api/download/{output_filename}'
                }
        
        except Exception as e:
            with tasks_lock:
                tasks[task_id] = {
                    'status': 'error',
                    'message': str(e)
                }
    
    thread = threading.Thread(target=process)
    thread.start()
    
    return jsonify({
        'success': True,
        'task_id': task_id
    })


@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    with tasks_lock:
        task = tasks.get(task_id, {})
    
    return jsonify(task)


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """下载文件"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    return send_file(filepath, as_attachment=True)


@app.route('/api/transitions', methods=['GET'])
def get_transitions():
    """获取可用转场效果"""
    from .transitions import TransitionManager
    tm = TransitionManager()
    
    return jsonify({
        'success': True,
        'transitions': tm.get_available_transitions()
    })


@app.route('/api/effects', methods=['GET'])
def get_effects():
    """获取可用特效"""
    effects = [
        {'name': 'speed', 'description': '速度调整'},
        {'name': 'brightness', 'description': '亮度调整'},
        {'name': 'contrast', 'description': '对比度调整'},
        {'name': 'saturation', 'description': '饱和度调整'},
        {'name': 'blur', 'description': '模糊'},
        {'name': 'sharpen', 'description': '锐化'},
        {'name': 'vintage', 'description': '复古效果'},
        {'name': 'black_white', 'description': '黑白效果'},
        {'name': 'zoom', 'description': '缩放'},
        {'name': 'shake', 'description': '抖动'},
    ]
    
    return jsonify({
        'success': True,
        'effects': effects
    })


def run_web(host='0.0.0.0', port=5000, debug=False):
    """运行 Web 服务"""
    # 确保目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_web(debug=True)
