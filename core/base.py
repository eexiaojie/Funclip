"""
基础类和接口定义 - Windows兼容版本
"""
import abc
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

class WindowsCompatibleBase:
    """Windows兼容基类"""
    
    def __init__(self):
        # Windows进程池配置
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(32, (os.cpu_count() or 1) + 4),
            thread_name_prefix="FunClip"
        )
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

@dataclass
class ProcessingResult:
    """处理结果数据类"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    file_path: Optional[Path] = None

class BaseModel(WindowsCompatibleBase, abc.ABC):
    """模型基类"""
    
    def __init__(self, model_path: Path, device: str = "cpu", **kwargs):
        super().__init__()
        self.model_path = Path(model_path)
        self.device = device
        self.model = None
        self.is_loaded = False
    
    @abc.abstractmethod
    def load_model(self) -> bool:
        """加载模型"""
        pass
    
    @abc.abstractmethod
    def predict(self, input_data: Any) -> ProcessingResult:
        """预测"""
        pass
    
    def unload_model(self):
        """卸载模型"""
        self.model = None
        self.is_loaded = False

class BaseProcessor(WindowsCompatibleBase, abc.ABC):
    """处理器基类"""
    
    @abc.abstractmethod
    def process(self, input_path: Path, **kwargs) -> ProcessingResult:
        """处理文件"""
        pass

class BaseService(WindowsCompatibleBase, abc.ABC):
    """服务基类"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.is_initialized = False
    
    @abc.abstractmethod
    def initialize(self) -> bool:
        """初始化服务"""
        pass