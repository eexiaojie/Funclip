"""
字幕处理器 - Windows版本
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import timedelta
from core.base import BaseProcessor, ProcessingResult
from core.exceptions import ProcessingError, handle_windows_exceptions
from utils.windows_utils import WindowsPathManager

class SubtitleProcessor(BaseProcessor):
    """字幕处理器"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.encoding = kwargs.get("encoding", "utf-8")
    
    @handle_windows_exceptions
    def process(self, input_data: Any, **kwargs) -> ProcessingResult:
        """处理字幕数据"""
        process_type = kwargs.get("type", "generate_srt")
        
        if process_type == "generate_srt":
            return self.generate_srt(input_data, **kwargs)
        elif process_type == "parse_srt":
            return self.parse_srt_file(input_data, **kwargs)
        elif process_type == "filter_by_speaker":
            return self.filter_by_speaker(input_data, **kwargs)
        elif process_type == "merge_segments":
            return self.merge_segments(input_data, **kwargs)
        else:
            return ProcessingResult(
                success=False,
                error=f"不支持的处理类型: {process_type}"
            )
    
    @handle_windows_exceptions
    def generate_srt(self, sentences: List[Dict], **kwargs) -> ProcessingResult:
        """生成SRT字幕文件"""
        try:
            output_path = kwargs.get("output_path")
            if not output_path:
                raise ProcessingError("缺少输出路径参数")
            
            output_path = WindowsPathManager.normalize_path(output_path)
            
            srt_content = []
            
            for i, sentence in enumerate(sentences, 1):
                start_time = sentence.get("start_time", 0)
                end_time = sentence.get("end_time", 0) 
                text = sentence.get("text", "").strip()
                speaker = sentence.get("speaker", "")
                
                if not text:
                    continue
                
                # 格式化时间
                start_srt = self._seconds_to_srt_time(start_time)
                end_srt = self._seconds_to_srt_time(end_time)
                
                # 添加说话人信息（如果有）
                if speaker and kwargs.get("include_speaker", False):
                    text = f"[{speaker}] {text}"
                
                # SRT格式
                srt_content.append(f"{i}")
                srt_content.append(f"{start_srt} --> {end_srt}")
                srt_content.append(text)
                srt_content.append("")  # 空行
            
            # 写入文件
            with open(output_path, 'w', encoding=self.encoding) as f:
                f.write('\n'.join(srt_content))
            
            return ProcessingResult(
                success=True,
                data={
                    "srt_path": output_path,
                    "subtitle_count": len(sentences),
                    "total_duration": sentences[-1].get("end_time", 0) if sentences else 0
                },
                file_path=output_path,
                metadata={"process_type": "generate_srt", "encoding": self.encoding}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"生成SRT失败: {e}"
            )
    
    @handle_windows_exceptions
    def parse_srt_file(self, srt_path: Path, **kwargs) -> ProcessingResult:
        """解析SRT字幕文件"""
        try:
            srt_path = WindowsPathManager.normalize_path(srt_path)
            
            if not srt_path.exists():
                raise ProcessingError("SRT文件不存在")
            
            with open(srt_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # 解析SRT内容
            sentences = self._parse_srt_content(content)
            
            return ProcessingResult(
                success=True,
                data={"sentences": sentences, "total_count": len(sentences)},
                metadata={"process_type": "parse_srt", "source_file": str(srt_path)}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"解析SRT失败: {e}"
            )
    
    def _parse_srt_content(self, content: str) -> List[Dict[str, Any]]:
        """解析SRT内容"""
        sentences = []
        
        # 按空行分割字幕块
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                # 解析序号
                index = int(lines[0])
                
                # 解析时间
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                if not time_match:
                    continue
                
                start_time = self._srt_time_to_seconds(time_match.group(1))
                end_time = self._srt_time_to_seconds(time_match.group(2))
                
                # 解析文本（可能有多行）
                text = '\n'.join(lines[2:])
                
                # 检查是否包含说话人信息
                speaker = ""
                speaker_match = re.match(r'\[([^\]]+)\]\s*(.*)', text)
                if speaker_match:
                    speaker = speaker_match.group(1)
                    text = speaker_match.group(2)
                
                sentences.append({
                    "index": index,
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text,
                    "speaker": speaker,
                    "duration": end_time - start_time
                })
                
            except (ValueError, IndexError):
                continue
        
        return sentences
    
    @handle_windows_exceptions
    def filter_by_speaker(self, sentences: List[Dict], **kwargs) -> ProcessingResult:
        """按说话人过滤字幕"""
        try:
            target_speakers = kwargs.get("speakers", [])
            if not target_speakers:
                return ProcessingResult(
                    success=False,
                    error="缺少目标说话人列表"
                )
            
            # 确保target_speakers是列表
            if isinstance(target_speakers, str):
                target_speakers = [target_speakers]
            
            filtered_sentences = []
            
            for sentence in sentences:
                speaker = sentence.get("speaker", "")
                if speaker in target_speakers:
                    filtered_sentences.append(sentence)
            
            return ProcessingResult(
                success=True,
                data={
                    "sentences": filtered_sentences,
                    "original_count": len(sentences),
                    "filtered_count": len(filtered_sentences),
                    "target_speakers": target_speakers
                },
                metadata={"process_type": "filter_by_speaker"}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"按说话人过滤失败: {e}"
            )
    
    @handle_windows_exceptions
    def merge_segments(self, sentences: List[Dict], **kwargs) -> ProcessingResult:
        """合并字幕段落"""
        try:
            max_gap = kwargs.get("max_gap", 1.0)  # 最大间隔时间（秒）
            max_duration = kwargs.get("max_duration", 30.0)  # 最大段落时长
            
            merged_segments = []
            current_segment = None
            
            for sentence in sentences:
                if current_segment is None:
	    # 开始新段落
                    current_segment### 5.3 模型模块 (models/)