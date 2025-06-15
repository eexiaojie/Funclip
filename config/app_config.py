"""
应用程序配置 - Windows优化版本
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppConfig:
    # Windows系统配置
    host: str = "127.0.0.1"
    port: int = 7860
    debug: bool = False
    
    # Windows路径配置
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = project_root / "data"
    models_dir: Path = data_dir / "models" 
    output_dir: Path = project_root / "output"
    temp_dir: Path = Path(os.environ.get("TEMP", "C:\\temp")) / "funclip"
    font_dir: Path = project_root / "fonts"
    
    # Windows进程配置
    max_workers: int = min(32, (os.cpu_count() or 1) + 4)
    chunk_size: int = 1024 * 1024  # 1MB chunks for Windows
    
    # Windows文件处理
    supported_video_formats: tuple = (".mp4", ".avi", ".mov", ".mkv", ".wmv")
    supported_audio_formats: tuple = (".wav", ".mp3", ".m4a", ".flac", ".wma")
    
    def __post_init__(self):
        # 确保Windows目录存在
        for directory in [self.data_dir, self.models_dir, self.output_dir, 
                         self.temp_dir, self.font_dir]:
            directory.mkdir(parents=True, exist_ok=True)