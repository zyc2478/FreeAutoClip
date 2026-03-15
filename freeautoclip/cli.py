#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命令行接口 - FreeAutoClip CLI
"""

import argparse
import os
import sys
from typing import List

from .core import VideoEditor
from .config import OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser(
        description="FreeAutoClip - 自动化视频剪辑工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动剪辑单个视频
  freeautoclip -i input.mp4 -o output.mp4
  
  # 智能切片
  freeautoclip -i input.mp4 --smart-cut --remove-silence
  
  # 批量处理
  freeautoclip --batch input1.mp4 input2.mp4 input3.mp4 -o ./output/
  
  # 应用特定风格
  freeautoclip -i input.mp4 --style energetic -o output.mp4
        """
    )
    
    # 输入输出
    parser.add_argument("-i", "--input", help="输入视频文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径或目录")
    parser.add_argument("--batch", nargs="+", help="批量处理多个视频")
    
    # 剪辑选项
    parser.add_argument("--smart-cut", action="store_true", 
                       help="使用智能切片")
    parser.add_argument("--remove-silence", action="store_true",
                       help="移除静音片段")
    parser.add_argument("--detect-highlights", action="store_true",
                       help="检测高光片段")
    parser.add_argument("--clip-duration", type=float, default=5.0,
                       help="固定切片时长（秒）")
    
    # 效果选项
    parser.add_argument("--style", choices=["dynamic", "calm", "energetic"],
                       default="dynamic", help="剪辑风格")
    parser.add_argument("--transitions", nargs="+",
                       help="转场效果类型列表")
    parser.add_argument("--no-transitions", action="store_true",
                       help="不使用转场效果")
    
    # 文字选项
    parser.add_argument("--add-text", help="添加文字")
    parser.add_argument("--text-position", default="bottom",
                       help="文字位置 (top/center/bottom)")
    parser.add_argument("--text-style", help="文字样式配置文件")
    
    # 音频选项
    parser.add_argument("--bgm", help="背景音乐路径")
    parser.add_argument("--bgm-volume", type=float, default=0.3,
                       help="背景音乐音量")
    
    # 输出选项
    parser.add_argument("--resolution", help="输出分辨率 (如 1920x1080)")
    parser.add_argument("--fps", type=int, default=30,
                       help="输出帧率")
    parser.add_argument("--bitrate", default="8000k",
                       help="输出码率")
    parser.add_argument("--format", default="mp4",
                       help="输出格式")
    
    # 其他选项
    parser.add_argument("--use-jianying", action="store_true",
                       help="使用剪映API")
    parser.add_argument("--save-project", help="保存项目配置文件")
    parser.add_argument("--load-project", help="加载项目配置文件")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="显示详细信息")
    parser.add_argument("--version", action="version",
                       version="%(prog)s 1.0.0")
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.input and not args.batch and not args.load_project:
        parser.error("需要提供输入文件 (--input)、批量处理 (--batch) 或加载项目 (--load-project)")
    
    # 初始化编辑器
    editor = VideoEditor(use_jianying_api=args.use_jianying)
    
    # 加载项目
    if args.load_project:
        if args.verbose:
            print(f"加载项目: {args.load_project}")
        editor.load_project(args.load_project)
    
    # 批量处理
    if args.batch:
        if not args.output:
            args.output = OUTPUT_DIR
        
        if args.verbose:
            print(f"批量处理 {len(args.batch)} 个视频...")
        
        output_paths = editor.batch_process(
            args.batch,
            output_dir=args.output,
            preset=args.style
        )
        
        print(f"\n完成！已处理 {len(output_paths)} 个视频")
        for path in output_paths:
            print(f"  - {path}")
        
        return
    
    # 单视频处理
    if args.input:
        if args.verbose:
            print(f"处理视频: {args.input}")
        
        # 设置输出路径
        if not args.output:
            base_name = os.path.splitext(os.path.basename(args.input))[0]
            args.output = os.path.join(OUTPUT_DIR, f"{base_name}_edited.mp4")
        
        # 自动剪辑
        if args.smart_cut or args.remove_silence or args.detect_highlights:
            segments = editor.smart_cut(
                args.input,
                remove_silence=args.remove_silence,
                detect_highlights=args.detect_highlights
            )
            if args.verbose:
                print(f"生成 {len(segments)} 个片段")
        else:
            # 固定时长切片
            segments = editor.cut_by_duration(args.input, args.clip_duration)
        
        # 加载片段
        editor.clips = []
        for segment in segments:
            clip_path = editor.cutter.export_segment(
                segment,
                os.path.join(OUTPUT_DIR, f"temp_clip_{segment.start:.2f}.mp4")
            )
            from moviepy.editor import VideoFileClip
            editor.clips.append(VideoFileClip(clip_path))
        
        # 应用转场
        if not args.no_transitions and len(editor.clips) > 1:
            if args.verbose:
                print("添加转场效果...")
            final = editor.transitions.auto_apply_transitions(
                editor.clips,
                transition_types=args.transitions
            )
            editor.clips = [final]
        
        # 应用风格特效
        if args.verbose:
            print(f"应用 {args.style} 风格...")
        
        if args.style == "dynamic":
            effects = [
                {"type": "contrast", "params": {"factor": 1.1}},
                {"type": "saturation", "params": {"factor": 1.2}},
            ]
        elif args.style == "calm":
            effects = [
                {"type": "brightness", "params": {"factor": 0.95}},
                {"type": "contrast", "params": {"factor": 0.95}},
            ]
        else:  # energetic
            effects = [
                {"type": "contrast", "params": {"factor": 1.2}},
                {"type": "saturation", "params": {"factor": 1.3}},
            ]
        
        editor.clips[0] = editor.effects.apply_chains(editor.clips[0], effects)
        
        # 添加文字
        if args.add_text:
            if args.verbose:
                print(f"添加文字: {args.add_text}")
            
            h_pos = "center"
            v_pos = args.text_position
            
            editor.add_text(
                args.add_text,
                position=(h_pos, v_pos),
                duration=editor.clips[0].duration
            )
        
        # 添加背景音乐
        if args.bgm:
            if args.verbose:
                print(f"添加背景音乐: {args.bgm}")
            editor.add_bgm(args.bgm, volume=args.bgm_volume)
        
        # 解析分辨率
        resolution = None
        if args.resolution:
            w, h = args.resolution.split("x")
            resolution = (int(w), int(h))
        
        # 导出
        if args.verbose:
            print(f"导出到: {args.output}")
        
        editor.export(
            args.output,
            resolution=resolution,
            fps=args.fps,
            bitrate=args.bitrate
        )
        
        print(f"✅ 完成！输出文件: {args.output}")
        
        # 保存项目
        if args.save_project:
            if args.verbose:
                print(f"保存项目: {args.save_project}")
            editor.save_project(args.save_project)


if __name__ == "__main__":
    main()
