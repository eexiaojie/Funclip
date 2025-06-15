"""
视频处理器 - Windows优化版本
"""
import subprocess
import cv2
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from core.base import BaseProcessor, ProcessingResult
from core.exceptions import ProcessingError, handle_windows_exceptions
from utils.windows_utils import WindowsPathManager
from utils.file_utils import get_ffmpeg_path

class VideoProcessor(BaseProcessor):
    """视频处理器"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.ffmpeg_path = get_ffmpeg_path()
        self.quality = kwargs.get("quality", "medium")  # low, medium, high
        self.codec = kwargs.get("codec", "libx264")
    
    @handle_windows_exceptions  
    def process(self, input_path: Path, **kwargs) -> ProcessingResult:
        """处理视频文件"""
        input_path = WindowsPathManager.normalize_path(input_path)
        
        process_type = kwargs.get("type", "clip")
        
        if process_type == "clip":
            return self.clip_video(input_path, **kwargs)
        elif process_type == "info":
            return self.get_video_info(input_path)
        elif process_type == "thumbnail":
            return self.generate_thumbnail(input_path, **kwargs)
        elif process_type == "concat":
            return self.concatenate_videos(kwargs.get("video_list", []), **kwargs)
        else:
            return ProcessingResult(
                success=False,
                error=f"不支持的处理类型: {process_type}"
            )
    
    @handle_windows_exceptions
    def clip_video(self, video_path: Path, segments: List[Dict], **kwargs) -> ProcessingResult:
        """视频剪辑"""
        try:
            output_dir = kwargs.get("output_dir", video_path.parent / "clips")
            WindowsPathManager.ensure_directory(output_dir)
            
            clipped_files = []
            
            for i, segment in enumerate(segments):
                start_time = segment.get("start_time", 0)
                end_time = segment.get("end_time", 0)
                
                if end_time <= start_time:
                    continue
                
                # 生成输出文件名
                segment_name = segment.get("name", f"clip_{i:03d}")
                safe_name = WindowsPathManager.get_safe_filename(segment_name)
                output_path = output_dir / f"{safe_name}.mp4"
                
                # 构建FFmpeg命令
                cmd = self._build_clip_command(
                    video_path, output_path, start_time, end_time, **kwargs
                )
                
                # 执行剪辑
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
                if result.returncode == 0 and output_path.exists():
                    # 获取剪辑后视频信息
                    clip_info = self._get_clip_info(output_path)
                    
                    clipped_files.append({
                        "segment_index": i,
                        "file_path": output_path,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": end_time - start_time,
                        "file_size": output_path.stat().st_size,
                        "clip_info": clip_info
                    })
                else:
                    print(f"剪辑失败 - 段落 {i}: {result.stderr}")
            
            return ProcessingResult(
                success=True,
                data={
                    "clips": clipped_files,
                    "total_clips": len(clipped_files),
                    "total_duration": sum(clip["duration"] for clip in clipped_files)
                },
                metadata={"process_type": "clip", "output_dir": str(output_dir)}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"视频剪辑失败: {e}"
            )
    
    def _build_clip_command(self, input_path: Path, output_path: Path, 
                           start_time: float, end_time: float, **kwargs) -> List[str]:
        """构建FFmpeg剪辑命令"""
        duration = end_time - start_time
        
        # 基础命令
        cmd = [
            str(self.ffmpeg_path),
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(duration),
        ]
        
        # 视频编码参数
        if kwargs.get("video_codec"):
            cmd.extend(["-c:v", kwargs["video_codec"]])
        else:
            cmd.extend(["-c:v", self.codec])
        
        # 音频编码参数
        if kwargs.get("audio_codec"):
            cmd.extend(["-c:a", kwargs["audio_codec"]])
        else:
            cmd.extend(["-c:a", "aac"])
        
        # 质量设置
        if self.quality == "high":
            cmd.extend(["-crf", "18", "-preset", "slow"])
        elif self.quality == "medium":
            cmd.extend(["-crf", "23", "-preset", "medium"])
        else:  # low
            cmd.extend(["-crf", "28", "-preset", "fast"])
        
        # 输出参数
        cmd.extend([
            "-avoid_negative_ts", "make_zero",
            "-y",  # 覆盖输出文件
            str(output_path)
        ])
        
        return cmd
    
    @handle_windows_exceptions
    def get_video_info(self, video_path: Path) -> ProcessingResult:
        """获取视频信息"""
        try:
            # 使用OpenCV获取基本信息
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                raise ProcessingError("无法打开视频文件")
            
            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            # 获取文件大小
            file_size = video_path.stat().st_size
            
            video_info = {
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "resolution": f"{width}x{height}",
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            }
            
            return ProcessingResult(
                success=True,
                data=video_info,
                metadata={"process_type": "info"}
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"获取视频信息失败: {e}"
            )
    
    def _get_clip_info(self, clip_path: Path) -> Dict[str, Any]:
        """获取剪辑片段信息"""
        result = self.get_video_info(clip_path)
        return result.data if result.success else {}
    
    @handle_windows_exceptions
    def generate_thumbnail(self, video_path: Path, **kwargs) -> ProcessingResult:
        """生成视频缩略图"""
        try:
            timestamp = kwargs.get("timestamp", 1.0)  # 默认第1秒
            output_path = kwargs.get("output_path")
            
            if not output_path:
                output_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
            else:
                output_path = WindowsPathManager.normalize_path(output_path)
            
            cmd = [
                str(self.ffmpeg_path),
                "-i", str(video_path),
                "-ss", str(timestamp),
                "-vframes", "1",
                "-q:v", "2",
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
                return ProcessingResult(
                    success=True,
                    data={"thumbnail_path": output_path, "timestamp": timestamp},
                    file_path=output_path,
                    metadata={"process_type": "thumbnail"}
                )
            else:
                raise ProcessingError(f"FFmpeg错误: {result.stderr}")
                
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"生成缩略图失败: {e}"
            )