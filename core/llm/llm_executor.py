import re
import asyncio
from typing import Callable, Optional, Any, List
from core.llm.token_splitter import split_text_by_tokens
import tiktoken
import json

TERMINATION_PATTERNS = [
    r"\.{3,}\s*$",         # ... or ......
    r"(TERMINATE|END|CONTINUE|TO BE CONTINUED)\s*$"
]

def _seems_incomplete(text: str) -> bool:
    """检查文本是否看起来不完整，使用简单的字符串操作而不是正则表达式"""
    print(f"🔍 检查文本完整性 (最后100字符: {text[-100:] if len(text) > 100 else text})")
    if not text:
        print("⚠️ 空文本")
        return False
        
    # 只检查最后100个字符，避免处理过长的文本
    last_part = text[-100:].strip().upper()
    
    # 简单的字符串检查，不使用正则
    if last_part.endswith('...'):
        print("📝 检测到省略号结尾")
        return True
    if last_part.endswith('CONTINUE'):
        print("📝 检测到CONTINUE结尾")
        return True
    if last_part.endswith('TO BE CONTINUED'):
        print("📝 检测到TO BE CONTINUED结尾")
        return True
    if last_part.endswith('END'):
        print("📝 检测到END结尾")
        return True
    if last_part.endswith('TERMINATE'):
        print("📝 检测到TERMINATE结尾")
        return True
        
    print("✅ 文本完整")
    return False

async def mock_llm_call(prompt: str, return_json: bool = False) -> Any:
    """提供模拟的LLM响应，用于测试或无法连接LLM的情况
    
    Args:
        prompt: 提示词
        return_json: 是否返回JSON格式
        
    Returns:
        模拟的LLM响应
    """
    print("⚠️ 使用模拟LLM响应")
    
    # 模拟处理延迟
    await asyncio.sleep(1)
    
    # 检测提示中是否要求JSON格式
    json_requested = return_json or "JSON" in prompt or "json" in prompt
    
    if json_requested:
        # 返回一个基本的JSON结构
        response = {
            "status": "success",
            "message": "这是模拟的LLM JSON响应",
            "timestamp": str(asyncio.get_event_loop().time()),
            "data": {
                "analysis": "这是一个模拟分析结果",
                "details": ["项目1", "项目2", "项目3"],
                "recommendation": "这是一个模拟推荐"
            }
        }
        return response
    else:
        # 返回文本响应
        return """这是模拟的LLM文本响应。在实际应用中，这里会返回一个真实的LLM生成内容。
        
该响应用于开发和测试阶段，不应在生产环境中使用。请确保在生产环境中连接实际的LLM服务。"""

async def _run_with_continuation(
    chat: Callable[..., asyncio.Future],
    task: Optional[str] = None,
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    max_steps: int = 3,
    model: str = "gpt-4o"
) -> str:
    """运行带有自动继续功能的聊天，使用非递归方式处理响应"""
    print(f"\n🔄 开始运行continuation (max_steps={max_steps})")
    assert task or (system_prompt and user_prompt), "必须提供task或(system_prompt和user_prompt)"

    # 准备初始提示
    if task:
        print(f"📝 使用task模式 (长度: {len(task)}字符)")
        current_messages = [{"role": "user", "content": task}]
    else:
        print(f"📝 使用system+user模式 (system长度: {len(system_prompt or '')}字符, user长度: {len(user_prompt or '')}字符)")
        current_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    # 收集所有响应
    all_responses = []
    
    # 迭代处理，最多max_steps次
    for step in range(max_steps):
        try:
            print(f"\n🔄 开始第 {step+1} 步处理")
            print(f"📤 发送消息 (数量: {len(current_messages)})")
            
            # 发送请求
            result = await chat(messages=current_messages, model=model)
            
            # 获取响应文本
            response_text = result if isinstance(result, str) else result.messages[-1].content
            print(f"📥 收到响应 (长度: {len(response_text)}字符)")
            all_responses.append(response_text.strip())
            
            # 检查是否需要继续
            if not _seems_incomplete(response_text):
                print("✅ 响应完整，结束处理")
                break
                
            print(f"🔁 检测到不完整的输出 (步骤 {step+1})，继续...")
            
            # 添加继续提示
            current_messages.append({"role": "assistant", "content": response_text})
            current_messages.append({"role": "user", "content": "请继续上一个回答。"})
            
        except Exception as e:
            print(f"⚠️ 步骤 {step+1} 出错: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误详情: {str(e)}")
            break

    # 合并所有响应
    final_response = "\n".join(all_responses).strip()
    print(f"✅ continuation完成 (最终长度: {len(final_response)}字符)")
    return final_response

def _merge_sections(acc, current, depth=0):
    """非递归的合并逻辑，简单地将结果收集到列表中
    
    Args:
        acc: 累积的结果
        current: 当前需要合并的结果
        depth: 递归深度（此参数保留但不再使用）
        
    Returns:
        合并后的结果
    """
    print("🔄 收集新的数据块")
    
    # 如果没有之前的结果，创建新列表
    if not hasattr(_merge_sections, 'all_results'):
        _merge_sections.all_results = []
    
    # 添加新的结果到列表
    if current:
        _merge_sections.all_results.append(current)
        print(f"📦 已收集 {len(_merge_sections.all_results)} 个数据块")
    
    # 如果acc为空，返回当前结果
    if not acc:
        return current
    
    # 否则返回acc
    return acc

async def run_prompt(
    chat: Callable = None,
    *,
    messages: Optional[List[dict]] = None,
    user_message: Optional[str] = None,
    system_message: Optional[str] = None,
    model: str = "gpt-4o",
    tokenizer=None,
    max_input_tokens: int = 16000,  # 增大最大输入token数
    parse_response: Callable[[str], Any] = lambda x: x,
    merge_result: Callable[[Any, Any], Any] = lambda acc, x: x,
    get_system_prompt: Optional[Callable[[int, int], str]] = None,
    use_pipeline: bool = False,
    use_mock: bool = False,
    return_json: bool = False
) -> Any:
    """
    统一的 LLM prompt 调用接口。

    参数优先级：
    1. messages：完整历史，直接传递给 LLM。
    2. system_message + user_message：组装成 system+user 两条消息。
    3. user_message：单轮 user 消息。

    Args:
        chat: LLM 聊天函数。
        messages: 完整消息历史（List[Dict]）。
        user_message: 单轮 user 消息。
        system_message: 单轮 system 消息。
        model: 模型名称。
        tokenizer: 分词器。
        max_input_tokens: 最大输入 token 数。
        parse_response: 解析响应的函数。
        merge_result: 合并结果的函数。
        get_system_prompt: 分块时自定义 system prompt。
        use_pipeline: 是否流水线处理。
        use_mock: 是否使用模拟响应。
        return_json: 是否返回 JSON。
    Returns:
        LLM 响应结果。
    """
    print(f"\n🚀 开始运行prompt (模型: {model})")
    print(f"📊 配置: max_input_tokens={max_input_tokens}, use_mock={use_mock}")

    # 优先级：messages > (system_message + user_message) > user_message
    if messages:
        input_messages = messages
    elif system_message and user_message:
        input_messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    elif user_message:
        input_messages = [
            {"role": "user", "content": user_message}
        ]
    else:
        raise ValueError("必须提供 messages，或 (system_message + user_message)，或 user_message 其中之一")

    # 如果请求使用模拟响应，直接返回
    if use_mock or (chat is None):
        print("🔄 使用模拟LLM响应")
        combined_prompt = "\n".join([m.get("content", "") for m in input_messages])
        return await mock_llm_call(combined_prompt, return_json)

    # 自动创建tokenizer
    if tokenizer is None:
        print(f"📝 自动创建tokenizer (模型: {model})")
        tokenizer = tiktoken.encoding_for_model(model)
        print("✅ tokenizer创建成功")

    # 计算 token 数
    input_text = "\n".join([m.get("content", "") for m in input_messages])
    try:
        tokens = tokenizer.encode(input_text)
        token_count = len(tokens)
        print(f"📝 输入文本统计:")
        print(f"  - 字符数: {len(input_text)}")
        print(f"  - Token数: {token_count}")
        print(f"  - Token/字符比: {token_count/len(input_text):.2f}")
    except Exception as e:
        print(f"⚠️ Token计算出错: {str(e)}")
        raise

    # 如果文本足够短，直接处理
    if token_count <= max_input_tokens:
        print(f"📝 文本在允许范围内，直接发送")
        try:
            result = await chat(messages=input_messages, model=model)
            parsed = parse_response(result if isinstance(result, str) else result)
            print("✅ 直接处理完成")
            return parsed
        except Exception as e:
            print(f"⚠️ 直接处理时出错: {str(e)}")
            raise

    # 分块处理长文本
    print(f"\n📝 文本过长，开始分块处理")
    try:
        print("🔄 调用split_text_by_tokens...")
        chunks = split_text_by_tokens(input_text, tokenizer, max_tokens=max_input_tokens)
        print(f"📦 分块完成: {len(chunks)} 个块")
        for i, chunk in enumerate(chunks):
            chunk_tokens = len(tokenizer.encode(chunk))
            print(f"  块 {i+1}: {len(chunk)}字符, {chunk_tokens} tokens")
    except Exception as e:
        print(f"⚠️ 分块过程出错: {str(e)}")
        raise

    # 限制块数量
    if len(chunks) > 10:
        print(f"⚠️ 块数量过多 ({len(chunks)})，限制为前10个块")
        chunks = chunks[:10]

    # 处理每个块
    final_result = None
    for i, chunk in enumerate(chunks):
        print(f"\n🛰️ 开始处理块 {i+1}/{len(chunks)}")
        print(f"📊 块大小: {len(chunk)}字符, {len(tokenizer.encode(chunk))} tokens")
        # 分块时可自定义 system prompt
        if get_system_prompt:
            current_system_message = get_system_prompt(i + 1, len(chunks))
        else:
            current_system_message = system_message
        chunk_messages = (
            [{"role": "system", "content": current_system_message}] if current_system_message else []
        ) + [{"role": "user", "content": chunk}]
        try:
            response = await chat(messages=chunk_messages, model=model)
            parsed = parse_response(response if isinstance(response, str) else response)
            print(f"✅ 块 {i+1} 处理完成")
            if final_result is None:
                final_result = parsed
                print("📝 设置初始结果")
            else:
                print("🔄 合并结果...")
                final_result = merge_result(final_result, parsed)
                print("✅ 结果合并完成")
        except Exception as e:
            print(f"⚠️ 处理块 {i+1} 时出错:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误详情: {str(e)}")
            continue
    print("\n✅ 所有块处理完成")
    return final_result
