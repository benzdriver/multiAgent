#!/usr/bin/env python
"""
运行新版Clarifier，使用OpenAI作为LLM提供者
"""
import asyncio
from core.clarifier.clarifier import Clarifier
from core.llm.chat_openai import chat as openai_chat

async def main():
    # 创建Clarifier实例，传入LLM调用函数
    clarifier = Clarifier(llm_chat=openai_chat)
    
    # 启动Clarifier
    await clarifier.start()

if __name__ == "__main__":
    asyncio.run(main())  