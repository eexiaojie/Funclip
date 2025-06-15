#### processors/audio_processor.py
```python
"""
音频处理器 - Windows优化版本
"""
import subprocess
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from core.base import BaseProcessor, ProcessingResult
from core.exceptions import ProcessingError, handle_windows_exceptions
from utils.windows_utils import WindowsPathManager
from utils.file_utils import get_ffmpeg_path

class AudioProcessor(BaseProcessor):
    """音频处理器"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.sample_rate = kwargs.get("sample_rate", 16000)
        self.channels = kwargs.get("channels", 1)
        self.ffmpeg_path = get_ffmpeg_path()
    
    @handle_windows_exceptions
    def process(self, input_path: Path, **kwargs) -> ProcessingResult:
        """处理音频文件"""
        input_path = WindowsPathManager.normalize_path(input_path)
        
        # 根据处理类型选择方法
        process_type = kwargs.get("type", "extract")
        
        if process_type == "extract":
            return self.extract_audio_from_video(input_path, **kwargs)
        elif process_type == "normalize":
            return self.normalize_audio(input_path, **kwargs)
        elif process_type == "segment":
            return self.segment_audio(input_path, **kwargs)
        else:
            return ProcessingResult(
                success=False,
                error=f"不支持的处理类型: {process_type}"
            )
    
    @handle_windows_exceptions
    def extract_audio_from_video(self, video_path: Path, **kwargs) -> ProcessingResult:
        """从视频中提取音频"""
        try:
            output_path = kwargs.get("output_path")
            if not output_path:
                output_path = video_path.parent / f"{video_path.stem}_audio.wav"
            else:
                output_path = WindowsPathManager.normalize_path(output_path)
            
            # 使用FFmpeg提取音频（Windows路径处理）
            cmd = [
                str(self.ffmpeg_path),
                "-i", str(video_path),
                "-vn",  # 禁用视频
                "-acodec", "pcm_s16le",  # 16-bit PCM
                "-ar", str(self.sample_rate),  # 采样率
                "-ac", str(self.channels),  # 声道数
                "-y",  # 覆盖输出文件
                str(output_path)
            ]
            
            # Windows子进程处理
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            if result.returncode != 0:
                raise ProcessingError(f"FFmpeg错误: {result.stderr}")
            
            # 验证输出文件
            if not output_path.exists():
                raise ProcessingError("音频提取失败，输出文件不存在")
            
            # 获取音频信息
            audio_info = self.get_audio_info(output_path)
            
            return ProcessingResult(
                success=True,
                data=audio_info,
                file_path=output_path,
                metadata={"process_type": "extract", "original_video": str(video_path)}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"音频提取失败: {e}"
            )
    
    @handle_windows_exceptions
    def normalize_audio(self, audio_path: Path, **kwargs) -> ProcessingResult:
        """音频标准化处理"""
        try:
            # 使用librosa加载音频
            y, sr = librosa.load(str(audio_path), sr=self.sample_rate, mono=True)
            
            # 音频标准化
            y_normalized = librosa.util.normalize(y)
            
            # 去除静音段（可选）
            if kwargs.get("remove_silence", False):
                y_trimmed, _ = librosa.effects.trim(
                    y_normalized,
                    top_db=kwargs.get("silence_threshold", 20)
                )
                y_normalized = y_trimmed
            
            # 保存处理后的音频
            output_path = kwargs.get("output_path")
            if not output_path:
                output_path = audio_path.parent / f"{audio_path.stem}_normalized.wav"
            else:
                output_path = WindowsPathManager.normalize_path(output_path)
            
            sf.write(str(output_path), y_normalized, self.sample_rate)
            
            return ProcessingResult(
                success=True,
                data={"duration": len(y_normalized) / self.sample_rate},
                file_path=output_path,
                metadata={"process_type": "normalize"}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"音频标准化失败: {e}"
            )
    
    @handle_windows_exceptions
    def segment_audio(self, audio_path: Path, segments: list, **kwargs) -> ProcessingResult:
        """音频分段处理"""
        try:
            output_dir = kwargs.get("output_dir", audio_path.parent / "segments")
            WindowsPathManager.ensure_directory(output_dir)
            
            segmented_files = []
            
            for i, segment in enumerate(segments):
                start_time = segment.get("start_time", 0)
                end_time = segment.get("end_time", 0)
                
                if end_time <= start_time:
                    continue
                
                # 生成输出文件名
                segment_name = segment.get("name", f"segment_{i:03d}")
                safe_name = WindowsPathManager.get_safe_filename(segment_name)
                output_path = output_dir / f"{safe_name}.wav"
                
                # 使用FFmpeg分段
                cmd = [
                    str(self.ffmpeg_path),
                    "-i", str(audio_path),
                    "-ss", str(start_time),
                    "-t", str(end_time - start_time),
                    "-acodec", "copy",
                    "-y",
                    str(output_path)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
                if result.returncode == 0 and output_path.exists():
                    segmented_files.append({
                        "segment_index": i,
                        "file_path": output_path,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": end_time - start_time
                    })
            
            return ProcessingResult(
                success=True,
                data={"segments": segmented_files, "total_segments": len(segmented_files)},
                metadata={"process_type": "segment", "output_dir": str(output_dir)}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"音频分段失败: {e}"
            )
    
    def get_audio_info(self, audio_path: Path) -> Dict[str, Any]:
        """获取音频文件信息"""
        try:
            y, sr = librosa.load(str(audio_path), sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            return {
                "duration": duration,
                "sample_rate": sr,
                "channels": 1 if y.ndim == 1 else y.shape[0],
                "samples": len(y),
                "file_size": audio_path.stat().st_size
            }
        except Exception as e:
            return {"error": f"获取音频信息失败: {e}"}