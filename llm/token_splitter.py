from typing import List

def split_text_by_tokens(text: str, tokenizer, max_tokens: int = 2000) -> List[str]:
    """
    Splits a long text into chunks based on token limits.
    使用批量编码来减少tokenizer.encode的调用次数。

    Args:
        text: The full input string.
        tokenizer: A tiktoken tokenizer instance.
        max_tokens: Maximum number of tokens per chunk.

    Returns:
        A list of string chunks each under the token limit.
    """
    # 先对整个文本进行一次性编码
    try:
        all_tokens = tokenizer.encode(text)
        total_tokens = len(all_tokens)
        
        # 如果总token数小于max_tokens，直接返回原文本
        if total_tokens <= max_tokens:
            return [text]
        
        # 计算需要多少个块
        n_chunks = (total_tokens + max_tokens - 1) // max_tokens
        
        # 将tokens分成大致相等的几块
        chunk_size = total_tokens // n_chunks + 1
        chunks = []
        
        # 使用decode将token块转回文本
        start = 0
        while start < total_tokens:
            end = min(start + chunk_size, total_tokens)
            chunk_tokens = all_tokens[start:end]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            start = end
            
        return chunks
        
    except Exception as e:
        print(f"⚠️ Token分割出错，使用简单的字符分割: {str(e)}")
        # 如果tokenizer出错，使用简单的字符分割作为后备方案
        avg_chars_per_token = 4  # 假设平均每个token约4个字符
        char_limit = max_tokens * avg_chars_per_token
        
        # 简单地按字符数分割
        chunks = []
        for i in range(0, len(text), char_limit):
            chunks.append(text[i:i + char_limit])
        
        return chunks
