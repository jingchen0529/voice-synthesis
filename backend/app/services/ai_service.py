"""AI 文案生成服务 - 支持多个 AI Provider"""
import httpx
from typing import Optional, Dict, List
from enum import Enum
from pydantic import BaseModel
from app.core.config import settings


class AIProvider(str, Enum):
    """支持的 AI 服务商"""
    ZHIPU = "zhipu"      # 智谱AI - 可用
    QWEN = "qwen"        # 通义千问 - 可用
    DOUBAO = "doubao"    # 豆包 - 可用
    KIMI = "kimi"        # Kimi - 可用
    DEEPSEEK = "deepseek"  # DeepSeek - 暂不可用
    GROK = "grok"        # Grok - 暂不可用
    OPENAI = "openai"    # OpenAI - 暂不可用


class AIConfig(BaseModel):
    """AI 配置"""
    api_key: str
    base_url: str
    model: str
    available: bool = False


# AI Provider 配置映射（可用的排前面）
AI_PROVIDERS: Dict[str, Dict] = {
    AIProvider.ZHIPU: {
        "name": "智谱AI",
        "model": "glm-4-flash",
        "get_config": lambda: AIConfig(
            api_key=settings.ZHIPU_API_KEY,
            base_url=settings.ZHIPU_BASE_URL,
            model="glm-4-flash",
            available=bool(settings.ZHIPU_API_KEY)
        )
    },
    AIProvider.QWEN: {
        "name": "通义千问",
        "model": "qwen-plus",
        "get_config": lambda: AIConfig(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            model="qwen-plus",
            available=bool(settings.QWEN_API_KEY)
        )
    },
    AIProvider.DOUBAO: {
        "name": "豆包",
        "model": "doubao-seed-1-6-250615",
        "get_config": lambda: AIConfig(
            api_key=settings.DOUBAO_API_KEY,
            base_url=settings.DOUBAO_BASE_URL,
            model="doubao-seed-1-6-250615",
            available=bool(settings.DOUBAO_API_KEY)
        )
    },
    AIProvider.KIMI: {
        "name": "Kimi",
        "model": "moonshot-v1-8k",
        "get_config": lambda: AIConfig(
            api_key=settings.KIMI_API_KEY,
            base_url=settings.KIMI_BASE_URL,
            model="moonshot-v1-8k",
            available=bool(settings.KIMI_API_KEY)
        )
    },
    AIProvider.DEEPSEEK: {
        "name": "DeepSeek",
        "model": "deepseek-chat",
        "get_config": lambda: AIConfig(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            model="deepseek-chat",
            available=bool(settings.DEEPSEEK_API_KEY)
        )
    },
    AIProvider.GROK: {
        "name": "Grok",
        "model": "grok-3-mini-beta",
        "get_config": lambda: AIConfig(
            api_key=settings.GROK_API_KEY,
            base_url=settings.GROK_BASE_URL,
            model="grok-3-mini-beta",
            available=bool(settings.GROK_API_KEY)
        )
    },
    AIProvider.OPENAI: {
        "name": "OpenAI",
        "model": "gpt-4o-mini",
        "get_config": lambda: AIConfig(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model="gpt-4o-mini",
            available=bool(settings.OPENAI_API_KEY)
        )
    },
}


def get_available_providers() -> List[Dict]:
    """获取可用的 AI 服务商列表"""
    providers = []
    for provider_id, provider_info in AI_PROVIDERS.items():
        config = provider_info["get_config"]()
        providers.append({
            "id": provider_id,
            "name": provider_info["name"],
            "model": provider_info["model"],
            "available": config.available
        })
    return providers


def get_first_available_provider() -> Optional[str]:
    """获取第一个可用的 AI 服务商"""
    for provider_id, provider_info in AI_PROVIDERS.items():
        config = provider_info["get_config"]()
        if config.available:
            return provider_id
    return None


async def generate_script(
    topic: str,
    provider: str = "auto",
    style: str = "口播",
    duration: str = "1分钟",
    language: str = "zh"
) -> str:
    """
    使用 AI 生成视频文案
    
    Args:
        topic: 视频主题
        provider: AI 服务商 (auto 自动选择第一个可用的)
        style: 文案风格
        duration: 视频时长
        language: 语言
    
    Returns:
        生成的文案
    """
    # 自动选择 provider
    if provider == "auto":
        provider = get_first_available_provider()
        if not provider:
            raise ValueError("没有可用的 AI 服务，请配置 API Key")
    
    if provider not in AI_PROVIDERS:
        raise ValueError(f"不支持的 AI 服务商: {provider}")
    
    config = AI_PROVIDERS[provider]["get_config"]()
    if not config.available:
        raise ValueError(f"{AI_PROVIDERS[provider]['name']} 未配置 API Key")
    
    # 构建提示词
    prompt = f"""你是一个专业的短视频文案创作者。请根据以下要求创作一段视频文案：

主题：{topic}
风格：{style}
目标时长：{duration}
语言：{"中文" if language == "zh" else "English"}

要求：
1. 文案应该适合口播配音，语言自然流畅
2. 按照目标时长控制字数（中文约150字/分钟）
3. 开头要吸引人，结尾要有记忆点
4. 使用简短的句子，便于配音断句
5. 直接输出文案内容，不要添加任何说明或标题

文案："""

    # 调用 AI API（兼容 OpenAI 格式）
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{config.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "max_tokens": 2000
            }
        )
        
        if response.status_code != 200:
            error_detail = response.text
            raise Exception(f"AI 请求失败: {response.status_code} - {error_detail}")
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return content.strip()
