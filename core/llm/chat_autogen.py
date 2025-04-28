from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from llm.llm_executor import run_prompt
import tiktoken

tokenizer = tiktoken.encoding_for_model("gpt-4o")

async def chat(
    user_message: str = None,
    system_message: str = None,
    model: str = "gpt-4o",
    messages=None
):
    """
    使用Autogen模型进行聊天
    
    支持三种调用方式：
    1. messages: 直接传完整历史
    2. system_message + user_message: 组装 system+user
    3. user_message: 单轮 user 消息
    
    Args:
        user_message: 用户消息
        system_message: 系统提示
        model: 模型名称
        messages: 完整消息历史
    Returns:
        模型的回复
    """
    model_client = OpenAIChatCompletionClient(model=model)
    agent = AssistantAgent("CodeWriter", model_client=model_client)

    # 方式1：使用完整的消息历史
    if messages:
        return await agent.run(messages=messages)
    # 方式2：使用system_message + user_message
    elif system_message and user_message:
        formatted_messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        return await agent.run(messages=formatted_messages)
    # 方式3：只用user_message
    elif user_message:
        formatted_messages = [
            {"role": "user", "content": user_message}
        ]
        return await agent.run(messages=formatted_messages)
    else:
        raise ValueError("Must provide messages, or (system_message and user_message), or user_message")

