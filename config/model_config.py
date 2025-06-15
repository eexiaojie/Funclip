"""
模型配置 - 针对Windows系统优化
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

@dataclass 
class ModelConfig:
    # Windows模型路径
    models_base_dir: Path = Path(__file__).parent.parent / "data" / "models"
    
    # ASR模型配置
    asr_model_name: str = "speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
    asr_model_path: Path = models_base_dir / "paraformer"
    asr_device: str = "cpu"  # Windows默认CPU，可配置GPU
    asr_batch_size: int = 1
    
    # 说话人识别模型
    speaker_model_name: str = "speech_campplus_sv_zh-cn_16k-common"
    speaker_model_path: Path = models_base_dir / "campplus"
    speaker_device: str = "cpu"
    
    # LLM配置
    llm_providers: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.llm_providers is None:
            self.llm_providers = {
                "qwen": {
                    "api_key": "",
                    "base_url": "https://dashscope.aliyuncs.com/api/v1",
                    "model": "qwen-turbo"
                },
                "openai": {
                    "api_key": "", 
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-3.5-turbo"
                }
            }
        
        # 确保模型目录存在
        for path in [self.asr_model_path, self.speaker_model_path]:
            path.mkdir(parents=True, exist_ok=True)