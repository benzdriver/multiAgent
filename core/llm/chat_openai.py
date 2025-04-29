"""
Interface to OpenAI chat models
"""

import os
import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Optional, Union, Any

# Check if API key is present
api_key = os.environ.get("OPENAI_API_KEY_OPENAI_API_KEY")
if not api_key:
    print("⚠️ OPENAI_API_KEY_OPENAI_API_KEY环境变量未设置，OpenAI API调用将会失败")
    print("请设置OPENAI_API_KEY_OPENAI_API_KEY环境变量，或使用模拟响应模式")

client = None

def get_client():
    global client
    if client is None:
        if os.environ.get("USE_MOCK_LLM") == "True":
            mock_api_key = "sk-mock-key-for-testing"
            client = AsyncOpenAI(api_key=mock_api_key)
        else:
            client = AsyncOpenAI(api_key=api_key)
    return client

# Retry parameters
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

async def chat(
    system_message: Optional[str] = None,
    user_message: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stop: Optional[List[str]] = None,
    messages: Optional[List[Dict[str, str]]] = None
) -> Any:
    """
    Interact with OpenAI chat models
    
    支持三种调用方式：
    1. messages: 直接传完整历史
    2. system_message + user_message: 组装 system+user
    3. user_message: 单轮 user 消息
    
    Args:
        system_message: System prompt
        user_message: User message
        model: Model name
        temperature: Temperature parameter
        max_tokens: Maximum tokens to generate
        stop: List of stop tokens
        messages: Complete message history list
    Returns:
        Model response content
    """
    # 检查API密钥是否存在
    if not api_key:
        error_msg = "OpenAI API密钥未设置。请设置OPENAI_API_KEY环境变量。"
        print(f"❌ {error_msg}")
        return {
            "error": error_msg,
            "status": "api_key_missing"
        }
    # 构建消息列表
    if messages:
        message_list = messages
    elif system_message and user_message:
        message_list = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    elif user_message:
        message_list = [
            {"role": "user", "content": user_message}
        ]
    else:
        error_msg = "Must provide one of these parameter combinations: (messages), (system_message, user_message), or (user_message)"
        print(f"❌ {error_msg}")
        return {
            "error": error_msg,
            "status": "invalid_parameters"
        }
    # 使用迭代而不是递归的方式处理重试
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            print(f"🛰️ 发送OpenAI API请求 (尝试 {attempt+1}/{MAX_RETRIES})")
            current_client = get_client()
            response = await current_client.chat.completions.create(
                model=model,
                messages=message_list,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                print(f"⚠️ API请求失败: {str(e)[:200]}")
                print(f"⏳ {RETRY_DELAY}秒后重试...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"❌ OpenAI API请求在 {MAX_RETRIES} 次尝试后失败")
                break
    # 如果所有重试都失败，返回错误信息而不是抛出异常
    if last_error:
        error_msg = f"OpenAI API调用失败: {str(last_error)}"
        print(f"❌ {error_msg}")
        return {
            "error": error_msg,
            "status": "api_call_failed",
            "exception": str(last_error)
        }
    return {
        "error": "未知错误",
        "status": "unknown_error"
    }
