python"""
说话人识别模型 - Windows版本
"""
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from funasr import AutoModel
from core.base import BaseModel, ProcessingResult
from core.exceptions import ModelLoadError, handle_windows_exceptions
from utils.windows_utils import WindowsPathManager

class SpeakerModel(BaseModel):
    """说话人识别模型封装"""
    
    def __init__(self, model_path: Path, device: str = "cpu", **kwargs):
        super().__init__(model_path, device, **kwargs)
        self.num_speakers = kwargs.get("num_speakers", None)
        self.min_speakers = kwargs.get("min_speakers", 1)
        self.max_speakers = kwargs.get("max_speakers", 8)
    
    @handle_windows_exceptions
    def load_model(self) -> bool:
        """加载说话人识别模型"""
        try:
            model_path = WindowsPathManager.normalize_path(self.model_path)
            
            # 加载说话人分离模型
            self.diarization_model = AutoModel(
                model="cam++",
                model_revision="v2.0.2",
                device=self.device,
                cache_dir=str(model_path.parent)
            )
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            raise ModelLoadError(f"说话人识别模型加载失败: {e}")
    
    @handle_windows_exceptions  
    def predict(self, audio_path: Path, **kwargs) -> ProcessingResult:
        """说话人识别预测"""
        if not self.is_loaded:
            self.load_model()
        
        try:
            audio_path = WindowsPathManager.normalize_path(audio_path)
            
            # 执行说话人分离
            result = self.diarization_model.generate(
                input=str(audio_path),
                num_speakers=self.num_speakers,
                **kwargs
            )
            
            # 解析说话人结果
            speaker_result = self._parse_speaker_result(result)
            
            return ProcessingResult(
                success=True,
                data=speaker_result,
                metadata={"model": "cam++", "device": self.device}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"说话人识别失败: {e}"
            )
    
    def _parse_speaker_result(self, raw_result: Any) -> Dict[str, Any]:
        """解析说话人识别结果"""
        speakers = []
        speaker_segments = {}
        
        # 解析说话人时间段
        for segment in raw_result:
            speaker_id = segment.get("speaker", "spk0")
            start_time = segment.get("start", 0) / 1000
            end_time = segment.get("end", 0) / 1000
            
            if speaker_id not in speaker_segments:
                speaker_segments[speaker_id] = []
            
            speaker_segments[speaker_id].append({
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time
            })
        
        return {
            "speaker_segments": speaker_segments,
            "num_speakers": len(speaker_segments),
            "speakers": list(speaker_segments.keys())
        }
    
    def combine_with_asr(self, asr_result: Dict, speaker_result: Dict) -> Dict[str, Any]:
        """结合ASR和说话人识别结果"""
        combined_sentences = []
        
        for sentence in asr_result.get("sentences", []):
            # 根据时间段匹配说话人
            speaker_id = self._find_speaker_for_time(
                sentence["start_time"],
                sentence["end_time"], 
                speaker_result["speaker_segments"]
            )
            
            sentence["speaker"] = speaker_id
            combined_sentences.append(sentence)
        
        return {
            "sentences": combined_sentences,
            "speaker_info": speaker_result,
            "asr_info": asr_result
        }
    
    def _find_speaker_for_time(self, start_time: float, end_time: float, 
                              speaker_segments: Dict) -> str:
        """根据时间段查找对应的说话人"""
        max_overlap = 0
        best_speaker = "spk0"
        
        for speaker_id, segments in speaker_segments.items():
            for segment in segments:
                # 计算重叠时间
                overlap = min(end_time, segment["end_time"]) - max(start_time, segment["start_time"])
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = speaker_id
        
        return best_speaker