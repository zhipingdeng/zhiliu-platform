"""
LLM 客户端模块

提供统一的 LLM 调用接口，支持 OpenAI 兼容 API。
"""

from typing import List, Dict, Any, Optional
import httpx
from src.config.settings import get_settings


class LLMClient:
    """LLM 客户端类"""

    def __init__(self):
        settings = get_settings()
        self.model_name = settings.llm_model_name
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            模型回复内容
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# 全局客户端实例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def close_llm_client():
    """关闭 LLM 客户端"""
    global _llm_client
    if _llm_client:
        await _llm_client.close()
        _llm_client = None
