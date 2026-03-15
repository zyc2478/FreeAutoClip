#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FreeAutoClip 安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取 README
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "FreeAutoClip - 自动化视频剪辑工具"

# 读取 requirements
requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
with open(requirements_path, 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="freeautoclip",
    version="1.0.0",
    author="FreeAutoClip Team",
    author_email="",
    description="自动化视频剪辑工具 - 支持切片、转场、特效、合成、花字",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zyc2478/FreeAutoClip",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Video :: Non-Linear Editor",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "freeautoclip=freeautoclip.cli:main",
            "fac=freeautoclip.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "freeautoclip": [
            "templates/*.html",
            "static/*",
        ],
    },
    zip_safe=False,
)
