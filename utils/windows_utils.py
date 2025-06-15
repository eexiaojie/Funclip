"""
Windows系统特定工具函数
处理Windows路径、文件权限等
"""
import os
from pathlib import Path, PureWindowsPath
import tempfile

class WindowsPathManager:
    @staticmethod
    def normalize_path(path: str) -> Path:
        """标准化Windows路径"""
        return Path(path).resolve()
    
    @staticmethod
    def get_temp_dir() -> Path:
        """获取Windows临时目录"""
        return Path(tempfile.gettempdir()) / "funclip"
    
    @staticmethod
    def ensure_directory(path: Path) -> None:
        """确保目录存在，处理Windows权限"""
        path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """生成Windows安全的文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename