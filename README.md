# FunClip项目模块化重构设计规范
*基于Python 3.10 + Windows 10系统*

## 1. 项目概述

FunClip是一个开源的视频智能剪辑工具，集成了语音识别、说话人识别和大语言模型分析功能。本规范针对Windows 10系统和Python 3.10环境，将现有项目进行模块化重构，提高代码的可维护性和可扩展性。

## 2. 系统环境要求

### 2.1 基础环境
- **操作系统**: Windows 10/11 (64位)
- **Python版本**: Python 3.10.x
- **包管理器**: pip 22.0+
- **虚拟环境**: venv (Python内置)

### 2.2 外部依赖
- **FFmpeg**: 用于视频/音频处理
- **ImageMagick**: 用于字幕渲染
- **Visual Studio Build Tools**: 用于编译Python扩展包

## 3. 重构目标

- 将现有的单体代码拆分为独立的功能模块
- 优化Windows系统的文件路径处理
- 提供Windows友好的安装和部署方式
- 支持Windows系统的多进程和异步处理
- 便于在Windows开发环境中进行调试和测试

## 3. 模块化架构设计

### 3.1 项目目录结构
funclip/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── init.py
│   ├── app_config.py
│   ├── model_config.py
│   └── ui_config.py
├── core/
│   ├── init.py
│   ├── base.py
│   ├── exceptions.py
│   └── constants.py
├── models/
│   ├── init.py
│   ├── asr_model.py
│   ├── speaker_model.py
│   └── llm_model.py
├── processors/
│   ├── init.py
│   ├── audio_processor.py
│   ├── video_processor.py
│   ├── text_processor.py
│   └── subtitle_processor.py
├── services/
│   ├── init.py
│   ├── recognition_service.py
│   ├── clipping_service.py
│   ├── llm_service.py
│   └── export_service.py
├── utils/
│   ├── init.py
│   ├── file_utils.py
│   ├── time_utils.py
│   ├── validation_utils.py
│   └── logger.py
├── ui/
│   ├── init.py
│   ├── gradio_interface.py
│   ├── components/
│   │   ├── init.py
│   │   ├── upload_component.py
│   │   ├── recognition_component.py
│   │   ├── clipping_component.py
│   │   └── llm_component.py
│   └── assets/
│       ├── styles.css
│       └── scripts.js
├── api/
│   ├── init.py
│   ├── routes.py
│   ├── endpoints/
│   │   ├── init.py
│   │   ├── recognition.py
│   │   ├── clipping.py
│   │   └── llm.py
│   └── middleware/
│       ├── init.py
│       ├── auth.py
│       └── rate_limit.py
├── tests/
│   ├── init.py
│   ├── test_models/
│   ├── test_processors/
│   ├── test_services/
│   └── test_utils/
├── scripts/
│   ├── launch.py
│   ├── cli.py
│   └── install.py
├── data/
│   ├── models/
│   ├── fonts/
│   └── examples/
└── docs/
├── api.md
├── development.md
└── deployment.md

## 4. Windows系统特定配置

### 4.1 环境安装脚本 (scripts/install_windows.py)
```python
"""
Windows系统安装脚本
自动安装FFmpeg、ImageMagick等依赖
配置环境变量和PATH
"""
import os
import sys
import subprocess
import urllib.request
from pathlib import Path

class WindowsInstaller:
    def __init__(self):
        self.python_version = sys.version_info
        self.install_dir = Path(__file__).parent.parent
        
    def check_python_version(self):
        """检查Python版本是否为3.10"""
        if self.python_version.major != 3 or self.python_version.minor != 10:
            raise RuntimeError("需要Python 3.10版本")
    
    def install_ffmpeg(self):
        """安装FFmpeg到本地目录"""
        # 下载FFmpeg Windows版本
        # 配置环境变量
        pass
    
    def install_imagemagick(self):
        """安装ImageMagick"""
        # 下载ImageMagick Windows版本
        # 修改policy.xml配置
        pass
    
    def setup_virtual_env(self):
        """创建虚拟环境"""
        venv_path = self.install_dir / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
        return venv_path