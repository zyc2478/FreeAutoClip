#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FreeAutoClip 自动化剪辑测试脚本
演示完整的视频剪辑流程：切片、转场、特效、文字、合成
"""

import os
import sys
import numpy as np
from freeautoclip import VideoEditor
from freeautoclip.config import OUTPUT_DIR


def create_test_video(output_path: str = "test_input.mp4", duration: int = 10):
    """
    创建测试视频（使用 MoviePy 生成彩色动画视频）
    """
    print(f"正在创建测试视频: {output_path}")
    
    from freeautoclip.utils import VideoClip, ColorClip, CompositeVideoClip
    
    def make_frame(t):
        t_norm = t / duration
        r = int(255 * (0.5 + 0.5 * np.sin(2 * np.pi * t_norm)))
        g = int(255 * (0.5 + 0.5 * np.sin(2 * np.pi * t_norm + 2 * np.pi / 3)))
        b = int(255 * (0.5 + 0.5 * np.sin(2 * np.pi * t_norm + 4 * np.pi / 3)))
        return np.full((480, 640, 3), [r, g, b], dtype=np.uint8)
    
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_fps(30)
    clip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None)
    clip.close()
    
    print(f"✅ 测试视频创建成功: {output_path}")
    return output_path


def test_auto_editing(input_video: str, output_video: str = "test_output.mp4"):
    """
    测试自动化剪辑流程
    """
    print("\n" + "=" * 60)
    print("开始自动化剪辑测试")
    print("=" * 60)
    
    # 创建编辑器
    editor = VideoEditor()
    print("✅ 视频编辑器初始化完成")
    
    # 加载视频
    print(f"\n📹 加载视频: {input_video}")
    clip = editor.load_video(input_video)
    print(f"   - 时长: {clip.duration:.2f} 秒")
    print(f"   - 分辨率: {clip.size}")
    print(f"   - 帧率: {clip.fps} fps")
    
    # 智能切片
    print("\n✂️  执行智能切片...")
    segments = editor.smart_cut(
        input_video,
        remove_silence=False,  # 测试视频没有音频，跳过静音检测
        detect_highlights=True,
        min_clip_duration=2.0
    )
    print(f"   - 检测到 {len(segments)} 个片段")
    for i, seg in enumerate(segments[:5]):
        print(f"     片段 {i+1}: {seg.start:.2f}s - {seg.end:.2f}s ({seg.segment_type})")
    
    # 如果没有检测到片段，使用固定时长切片
    if len(segments) == 0:
        print("   - 使用固定时长切片...")
        segments = editor.cut_by_duration(input_video, clip_duration=3.0, overlap=0.5)
        print(f"   - 切片为 {len(segments)} 个片段")
    
    # 导出片段
    clips_dir = os.path.join(OUTPUT_DIR, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    print(f"\n📁 导出片段到: {clips_dir}")
    clip_paths = editor.cutter.batch_export(clips_dir, prefix="clip")
    print(f"   - 导出 {len(clip_paths)} 个片段")
    
    # 加载片段
    print("\n🎬 加载片段...")
    if len(clip_paths) > 0:
        editor.clips = [editor.load_video(path) for path in clip_paths]
        print(f"   - 加载 {len(editor.clips)} 个片段")
    else:
        # 直接从原始视频创建片段
        print(f"   - 直接从原始视频创建片段...")
        video = editor.load_video(input_video)
        editor.clips = []
        for seg in segments:
            clip_seg = video.subclipped(seg.start, seg.end)
            editor.clips.append(clip_seg)
        print(f"   - 创建 {len(editor.clips)} 个片段")
    
    # 添加转场
    print("\n✨ 添加转场效果...")
    try:
        editor.apply_transitions(["fade"], duration=0.5)
        print(f"   - 应用淡入淡出转场")
    except Exception as e:
        print(f"   - 转场效果跳过: {e}")
    
    # 添加特效
    print("\n🎨 添加视频特效...")
    try:
        editor.apply_effects([{"type": "brightness", "params": {"factor": 1.1}}])
        print(f"   - 应用亮度增强")
    except Exception as e:
        print(f"   - 特效跳过: {e}")
    
    # 添加文字
    print("\n📝 添加文字...")
    try:
        editor.add_text("FreeAutoClip", 
                       position=("center", "center"),
                       start_time=1.0,
                       duration=2.0,
                       style={"font_size": 60, "color": "white"})
        editor.add_text("自动化剪辑演示",
                       position=("center", "center"),
                       start_time=3.5,
                       duration=2.5,
                       style={"font_size": 40, "color": "yellow"})
        print(f"   - 添加 2 个文字层")
    except Exception as e:
        print(f"   - 文字跳过: {e}")
    
    # 合成视频
    print("\n🔗 合成视频...")
    # 转场已经合成了，直接使用第一个clip
    if len(editor.clips) > 0:
        final_video = editor.clips[0]
        print(f"   - 合成完成，时长: {final_video.duration:.2f} 秒")
    else:
        print("   - 没有可合成的视频")
        return None
    
    # 导出最终视频
    output_path = os.path.join(OUTPUT_DIR, output_video)
    print(f"\n💾 导出最终视频: {output_path}")
    try:
        editor.export(output_path)
    except Exception as e:
        print(f"   - 导出失败: {e}")
        return None
    
    # 清理
    print("\n🧹 清理临时文件...")
    for clip in editor.clips:
        try:
            clip.close()
        except:
            pass
    
    print("\n" + "=" * 60)
    print("✅ 自动化剪辑完成！")
    print("=" * 60)
    print(f"\n📁 输出文件: {output_path}")
    print(f"📁 片段目录: {clips_dir}")
    
    return output_path


def main():
    """主函数"""
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 创建测试视频
    test_video_path = os.path.join(OUTPUT_DIR, "test_input.mp4")
    if not os.path.exists(test_video_path):
        create_test_video(test_video_path, duration=15)
    else:
        print(f"使用已存在的测试视频: {test_video_path}")
    
    # 执行自动化剪辑
    output_path = test_auto_editing(test_video_path, "test_output.mp4")
    
    print("\n" + "🎉" * 30)
    print("测试完成！请查看输出视频效果")
    print("🎉" * 30)
    
    return output_path


if __name__ == "__main__":
    main()
