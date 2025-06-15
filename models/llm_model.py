python"""
大语言模型接口 - Windows版本
"""
import asyncio
import aiohttp
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator
from core.base import BaseModel, ProcessingResult
from core.exceptions import ModelLoadError, NetworkError, handle_windows_exceptions
from config.model_config import ModelConfig

class LLMModel(BaseModel):
    """大语言模型封装"""
    
    def __init__(self, provider: str = "qwen", **kwargs):
        self.provider = provider
        self.config = ModelConfig().llm_providers.get(provider, {})
        self.api_key = kwargs.get("api_key") or self.config.get("api_key")
        self.base_url = kwargs.get("base_url") or self.config.get("base_url")
        self.model_name = kwargs.get("model") or self.config.get("model")
        self.session = None
        super().__init__(Path(""), "cpu")  # LLM不需要本地路径
    
    @handle_windows_exceptions
    def load_model(self) -> bool:
        """初始化LLM连接"""
        if not self.api_key:
            raise ModelLoadError(f"缺少{self.provider}的API Key")
        
        self.is_loaded = True
        return True
    
    async def _create_session(self):
        """创建异步HTTP会话"""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            self.session = aiohttp.ClientSession(connector=connector)
    
    @handle_windows_exceptions
    async def predict_async(self, messages: List[Dict[str, str]], **kwargs) -> ProcessingResult:
        """异步LLM预测"""
        if not self.is_loaded:
            self.load_model()
        
        await self._create_session()
        
        try:
            headers = self._get_headers()
            payload = self._build_payload(messages, **kwargs)
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise NetworkError(f"LLM API错误 {response.status}: {error_text}")
                
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                
                return ProcessingResult(
                    success=True,
                    data={
                        "content": content,
                        "usage": result.get("usage", {}),
                        "model": self.model_name
                    },
                    metadata={"provider": self.provider}
                )
                
        except asyncio.TimeoutError:
            return ProcessingResult(
                success=False,
                error="LLM请求超时"
            )
        except Exception as e:
            return ProcessingResult(
                success=False, 
                error=f"LLM预测失败: {e}"
            )
    
    def predict(self, messages: List[Dict[str, str]], **kwargs) -> ProcessingResult:
        """同步LLM预测接口"""
        try:
            # Windows异步事件循环处理
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已有事件循环在运行，创建新任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.predict_async(messages, **kwargs)
                    )
                    return future.result(timeout=120)
            else:
                return asyncio.run(self.predict_async(messages, **kwargs))
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"同步预测失败: {e}"
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        if self.provider == "qwen":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "openai":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
    
    def _build_payload(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """构建请求负载"""
        return {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": False
        }
    
    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()
            self.session = None
        super().cleanup()

class LLMPromptManager:
    """LLM提示词管理器"""
    
    DEFAULT_PROMPTS = {
        "智能剪辑": """
基于以下视频字幕内容，请帮我分析并提取有价值的片段用于剪辑。

字幕内容：
{subtitles}

任务要求：
1. 识别视频中的关键信息点和亮点
2. 提取适合剪辑的时间段
3. 为每个片段提供简短的描述和理由

请以JSON格式返回结果：
{{
    "segments": [
        {{
            "start_time": "开始时间(秒)",
            "end_time": "结束时间(秒)", 
            "description": "片段描述",
            "reason": "推荐理由",
            "score": "推荐分数(1-10)"
        }}
    ]
}}
""",
        
        "内容总结": """
请基于以下视频字幕内容进行总结分析：

字幕内容：
{subtitles}

请提供：
1. 视频主要内容总结
2. 关键信息点提取
3. 重要时间节点标记
4. 适合制作短视频的片段推荐
""",
        
        "说话人分析": """
基于以下包含说话人信息的字幕，请进行说话人分析：

字幕内容：
{subtitles}

请分析：
1. 每个说话人的主要观点
2. 说话人之间的互动情况
3. 最有价值的对话片段
4. 推荐剪辑的精彩对话部分
"""
    }
    
    @classmethod
    def get_prompt(cls, prompt_type: str, **kwargs) -> str:
        """获取格式化的提示词"""
        template = cls.DEFAULT_PROMPTS.get(prompt_type, cls.DEFAULT_PROMPTS["智能剪辑"])
        return template.format(**kwargs)
    
    ### 5.4 处理器模块 (processors/)