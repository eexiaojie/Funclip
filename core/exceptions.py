"""
自定义异常类 - Windows错误处理优化
"""

class FunClipException(Exception):
    """FunClip基础异常类"""
    
    def __init__(self, message: str, details: str = None, error_code: int = None):
        self.message = message
        self.details = details
        self.error_code = error_code
        super().__init__(self.message)

class WindowsEnvironmentError(FunClipException):
    """Windows环境错误"""
    pass

class ModelLoadError(FunClipException):
    """模型加载异常"""
    pass

class ProcessingError(FunClipException):
    """处理异常"""
    pass

class FileOperationError(FunClipException):
    """文件操作异常 - Windows特定"""
    pass

class ValidationError(FunClipException):
    """验证异常"""
    pass

class NetworkError(FunClipException):
    """网络异常"""
    pass

# Windows特定异常处理装饰器
def handle_windows_exceptions(func):
    """处理Windows特定异常的装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PermissionError as e:
            raise FileOperationError(f"文件权限错误: {e}", error_code=403)
        except FileNotFoundError as e:
            raise FileOperationError(f"文件未找到: {e}", error_code=404)
        except OSError as e:
            if "cannot find the file specified" in str(e).lower():
                raise WindowsEnvironmentError(f"Windows环境错误: {e}", error_code=500)
            raise ProcessingError(f"系统错误: {e}", error_code=500)
        except Exception as e:
            raise FunClipException(f"未知错误: {e}", error_code=500)
    return wrapper