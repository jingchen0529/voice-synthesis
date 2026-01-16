"""测试所有 AI 服务商"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# AI 服务配置
PROVIDERS = {
    "zhipu": {
        "name": "智谱AI",
        "api_key": os.getenv("ZHIPU_API_KEY"),
        "base_url": os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
        "model": "glm-4-flash"
    },
    "qwen": {
        "name": "通义千问",
        "api_key": os.getenv("QWEN_API_KEY"),
        "base_url": os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "model": "qwen-plus"
    },
    "doubao": {
        "name": "豆包",
        "api_key": os.getenv("DOUBAO_API_KEY"),
        "base_url": os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        "model": "doubao-seed-1-6-250615"
    },
    "deepseek": {
        "name": "DeepSeek",
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "model": "deepseek-chat"
    },
    "grok": {
        "name": "Grok",
        "api_key": os.getenv("GROK_API_KEY"),
        "base_url": os.getenv("GROK_BASE_URL", "https://api.x.ai/v1"),
        "model": "grok-3-mini-beta"
    },
    "kimi": {
        "name": "Kimi",
        "api_key": os.getenv("KIMI_API_KEY"),
        "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
        "model": "moonshot-v1-8k"
    },
    "openai": {
        "name": "OpenAI",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": "gpt-4o-mini"
    },
}

async def test_provider(provider_id: str, config: dict) -> dict:
    """测试单个 AI 服务商"""
    result = {"id": provider_id, "name": config["name"], "status": "未配置", "message": ""}
    
    if not config["api_key"]:
        result["message"] = "API Key 未配置"
        return result
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config["model"],
                    "messages": [{"role": "user", "content": "说'测试成功'三个字"}],
                    "max_tokens": 50
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                result["status"] = "✅ 可用"
                result["message"] = content[:50]
            else:
                result["status"] = "❌ 失败"
                result["message"] = f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        result["status"] = "❌ 错误"
        result["message"] = str(e)[:100]
    
    return result

async def main():
    print("=" * 60)
    print("AI 服务商测试")
    print("=" * 60)
    
    tasks = [test_provider(pid, cfg) for pid, cfg in PROVIDERS.items()]
    results = await asyncio.gather(*tasks)
    
    for r in results:
        print(f"\n【{r['name']}】 {r['status']}")
        print(f"   {r['message']}")
    
    print("\n" + "=" * 60)
    available = [r for r in results if "可用" in r["status"]]
    print(f"可用服务: {len(available)}/{len(results)}")

if __name__ == "__main__":
    asyncio.run(main())
