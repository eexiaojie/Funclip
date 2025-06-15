```python
"""
语音识别模型 - Windows优化版本
"""
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from funasr import AutoModel
from core.base import BaseModel, ProcessingResult
from core.exceptions import ModelLoadError, handle_windows_exceptions
from utils.windows_utils import WindowsPathManager

class ASRModel(BaseModel):
    """语音识别模型封装"""
    
    def __init__(self, model_path: Path, device: str = "cpu", **kwargs):
        super().__init__(model_path, device, **kwargs)
        self.sample_rate = kwargs.get("sample_rate", 16000)
        self.batch_size = kwargs.get("batch_size", 1)
        self.hotwords = kwargs.get("hotwords", [])
        
    @handle_windows_exceptions
    def load_model(self) -> bool:
        """加载ASR模型"""
        try:
            # Windows路径处理
            model_path = WindowsPathManager.normalize_path(self.model_path)
            
            if not model_path.exists():
                # 自动下载模型到Windows本地路径
                self.model = AutoModel(
                    model="paraformer-zh",
                    model_revision="v2.0.4",
                    device=self.device,
                    cache_dir=str(model_path.parent)
                )
            else:
                self.model = AutoModel(
                    model=str(model_path),
                    device=self.device
                )
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            raise ModelLoadError(f"ASR模型加载失败: {e}")
    
    @handle_windows_exceptions
    def predict(self, audio_path: Path, **kwargs) -> ProcessingResult:
        """语音识别预测"""
        if not self.is_loaded:
            self.load_model()
        
        try:
            # Windows路径标准化
            audio_path = WindowsPathManager.normalize_path(audio_path)
            
            # 执行识别
            result = self.model.generate(
                input=str(audio_path),
                batch_size=self.batch_size,
                hotword=self.hotwords if self.hotwords else None,
                **kwargs
            )
            
            # 解析结果
            recognition_result = self._parse_result(result)
            
            return ProcessingResult(
                success=True,
                data=recognition_result,
                metadata={"model": "paraformer", "device": self.device}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"语音识别失败: {e}"
            )
    
    def _parse_result(self, raw_result: List[Dict]) -> Dict[str, Any]:
        """解析识别结果"""
        sentences = []
        
        for item in raw_result:
            if "text" in item:
                sentences.append({
                    "text": item["text"],
                    "start_time": item.get("timestamp", [[0, 0]])[0][0] / 1000,
                    "end_time": item.get("timestamp", [[0, 0]])[0][1] / 1000,
                    "confidence": item.get("confidence", 1.0)
                })
        
        return {
            "sentences": sentences,
            "full_text": " ".join([s["text"] for s in sentences]),
            "total_duration": sentences[-1]["end_time"] if sentences else 0
        }
    
    def set_hotwords(self, hotwords: List[str]):
        """设置热词"""
        self.hotwords = hotwords

class EnglishASRModel(ASRModel):
    """英文语音识别模型"""
    
    def __init__(self, model_path: Path, device: str = "cpu", **kwargs):
        super().__init__(model_path, device, **kwargs)
        self.language = "en"
    
    def load_model(self) -> bool:
        """加载英文ASR模型"""
        try:
            model_path = WindowsPathManager.normalize_path(self.model_path)
            
            self.model = AutoModel(
                model="paraformer-en",
                model_revision="v2.0.4", 
                device=self.device,
                cache_dir=str(model_path.parent)
            )
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            raise ModelLoadError(f"英文ASR模型加载失败: {e}")