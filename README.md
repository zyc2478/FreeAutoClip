# FreeAutoClip

🎬 **FreeAutoClip** - 智能自动化视频剪辑工具

支持自动化切片、转场、特效、合成、花字，无轨合一，一键完成剪辑工作。

## ✨ 功能特性

### 🎥 视频切片
- **智能切片** - 基于场景检测、音频分析自动识别片段
- **静音检测** - 自动识别并移除静音片段
- **高光检测** - 智能识别视频中的精彩片段
- **固定时长切片** - 按指定时长均匀切片

### 🎨 转场效果
- 淡入淡出 (Fade)
- 溶解 (Dissolve)
- 擦除 (Wipe)
- 滑动 (Slide)
- 缩放 (Zoom)
- 旋转 (Rotate)
- 模糊 (Blur)
- 像素化 (Pixelate)

### ✨ 视频特效
- 速度调整 (Speed)
- 亮度/对比度/饱和度调整
- 模糊/锐化
- 抖动效果 (Shake)
- Ken Burns 效果
- 复古效果 (Vintage)
- 黑白效果
- 暗角效果 (Vignette)

### 📝 花字/字幕
- 动态文字效果
- 多种动画（淡入、打字机、弹跳、滑动等）
- 描边和阴影
- 字幕自动同步
- 标题卡片
- 滚动字幕

### 🎵 音频处理
- 背景音乐自动同步
- 配音添加
- 音效管理
- 音量调节
- 淡入淡出

### 🔧 视频合成
- 多轨道合成
- 画中画 (Picture in Picture)
- 分屏效果
- 绿幕抠像
- 无轨合一

### 🌐 API 集成
- **剪映 API** - 支持调用剪映的自动化剪辑功能
- **CapCut API** - 支持国际版剪映 API

## 🚀 快速开始

### 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 启动 Web 界面

```bash
python run.py --mode web
```

访问 http://localhost:5000 使用 Web 界面

### 命令行使用

```bash
# 自动剪辑单个视频
python run.py --mode cli -i input.mp4 -o output.mp4

# 智能切片
python run.py --mode cli -i input.mp4 --smart-cut --remove-silence

# 批量处理
python run.py --mode cli --batch video1.mp4 video2.mp4 video3.mp4 -o ./output/

# 应用特定风格
python run.py --mode cli -i input.mp4 --style energetic -o output.mp4

# 添加背景音乐
python run.py --mode cli -i input.mp4 --bgm music.mp3 --bgm-volume 0.3 -o output.mp4
```

## 📖 Python API 使用

```python
from freeautoclip import VideoEditor

# 创建编辑器实例
editor = VideoEditor()

# 自动剪辑
result = editor.auto_edit(
    video_path="input.mp4",
    output_path="output.mp4",
    style="dynamic"  # dynamic, calm, energetic
)

# 智能切片
segments = editor.smart_cut(
    video_path="input.mp4",
    remove_silence=True,
    detect_highlights=True
)

# 应用特效链
effects = [
    {"type": "contrast", "params": {"factor": 1.2}},
    {"type": "saturation", "params": {"factor": 1.3}},
    {"type": "sharpen", "params": {"intensity": 1.5}},
]
editor.apply_effects(effects)

# 添加文字
editor.add_text(
    text="Hello World",
    position=("center", "bottom"),
    style={
        "font_size": 60,
        "font_color": "#FFFFFF",
        "animation": "fade_in"
    }
)

# 导出
editor.export("output.mp4")
```

## 🏗️ 项目结构

```
FreeAutoClip/
├── freeautoclip/           # 核心代码
│   ├── __init__.py
│   ├── core.py            # 主编辑器类
│   ├── cutter.py          # 视频切片
│   ├── transitions.py     # 转场效果
│   ├── effects.py         # 视频特效
│   ├── composer.py        # 视频合成
│   ├── text.py            # 花字/字幕
│   ├── config.py          # 配置文件
│   ├── cli.py             # 命令行接口
│   ├── web_interface.py   # Web 界面
│   └── api/               # API 集成
│       ├── __init__.py
│       ├── jianying_api.py
│       └── capcut_api.py
├── templates/             # Web 模板
│   └── editor.html
├── static/               # 静态文件
├── output/               # 输出目录
├── temp/                 # 临时文件
├── assets/               # 资源文件
│   ├── fonts/           # 字体
│   ├── music/           # 音乐
│   └── effects/         # 特效素材
├── run.py               # 启动脚本
├── setup.py             # 安装脚本
├── requirements.txt     # 依赖列表
└── README.md            # 说明文档
```

## ⚙️ 配置

### 环境变量

```bash
# 剪映 API 配置
export JIANYING_APP_KEY="your_app_key"
export JIANYING_APP_SECRET="your_app_secret"

# CapCut API 配置
export CAPCUT_API_KEY="your_api_key"
export CAPCUT_API_SECRET="your_api_secret"
```

### 配置文件

编辑 `freeautoclip/config.py` 修改默认配置：

- 视频分辨率、帧率、码率
- 切片参数
- 转场时长
- 特效参数
- 文字样式

## 🛠️ 高级功能

### 使用剪映 API

```python
from freeautoclip import VideoEditor

# 启用剪映 API
editor = VideoEditor(use_jianying_api=True)

# 自动剪辑（使用剪映云端能力）
result = editor.jianying_api.auto_edit(
    media_files=["video1.mp4", "video2.mp4"],
    template="auto"
)
```

### 批量处理

```python
from freeautoclip import VideoEditor

editor = VideoEditor()

# 批量处理
output_paths = editor.batch_process(
    video_paths=["video1.mp4", "video2.mp4", "video3.mp4"],
    output_dir="./output",
    preset="dynamic"
)
```

### 自定义特效链

```python
effects_chain = [
    {"type": "speed", "params": {"speed_factor": 1.5}},
    {"type": "brightness", "params": {"factor": 1.2}},
    {"type": "contrast", "params": {"factor": 1.1}},
    {"type": "saturation", "params": {"factor": 1.3}},
    {"type": "sharpen", "params": {"intensity": 1.0}},
    {"type": "vignette", "params": {"intensity": 0.3}},
]

editor.apply_effects(effects_chain)
```

## 📋 系统要求

- Python 3.8+
- FFmpeg（用于视频处理）
- 4GB+ RAM（推荐 8GB+）
- 支持的操作系统：Windows, macOS, Linux

## 🔧 安装 FFmpeg

### macOS
```bash
brew install ffmpeg
```

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Windows
下载并安装：https://ffmpeg.org/download.html

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [MoviePy](https://github.com/Zulko/moviepy) - 视频处理
- [OpenCV](https://opencv.org/) - 计算机视觉
- [Librosa](https://librosa.org/) - 音频分析
- [Flask](https://flask.palletsprojects.com/) - Web 框架

---

Made with ❤️ by FreeAutoClip Team
# FreeAutoClip
