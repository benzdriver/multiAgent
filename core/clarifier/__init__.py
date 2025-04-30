"""
核心Clarifier模块初始化文件
提供工厂方法和工具函数，简化Clarifier的创建和使用
"""

import os
import importlib
from typing import Optional, Dict, Any, Callable
from pathlib import Path

def create_clarifier(
    data_dir: str = "data",
    use_mock: bool = False, 
    model: str = "gpt-4o",
    verbose: bool = True
) -> Any:
    """
    创建并配置Clarifier实例的工厂方法
    
    Args:
        data_dir: 数据目录
        use_mock: 是否强制使用模拟LLM，即使有API密钥
        model: 默认使用的模型
        verbose: 是否输出详细日志
    
    Returns:
        配置好的Clarifier实例
    """
    # 导入核心模块
    from .clarifier import Clarifier
    from .architecture_manager import ArchitectureManager
    
    # 只有在需要真实API时才导入llm模块
    if not use_mock:
        try:
            # 检查API密钥
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                if verbose:
                    print("⚠️ 未找到OpenAI API密钥。将使用模拟LLM响应。")
                llm_chat = None  # 使用模拟模式
            else:
                # 动态导入以减少依赖
                print("🔍 尝试导入core.llm.chat_openai模块...")
                openai_module = importlib.import_module("core.llm.chat_openai")
                print("✅ 成功导入core.llm.chat_openai模块")
                llm_chat = openai_module.chat
                print(f"✅ 成功获取chat函数: {llm_chat}")
                if verbose:
                    print("✓ 找到OpenAI API密钥。将使用真实LLM响应。")
        except ImportError:
            if verbose:
                print("⚠️ 无法导入core.llm.chat_openai模块。将使用模拟LLM响应。")
            llm_chat = None
    else:
        llm_chat = None
        if verbose:
            print("ℹ️ 已配置为使用模拟LLM响应。")
    
    # 创建Clarifier实例
    clarifier = Clarifier(data_dir=data_dir, llm_chat=llm_chat)
    
    # 创建并关联ArchitectureManager
    architecture_manager = ArchitectureManager()
    clarifier.architecture_manager = architecture_manager
    
    return clarifier

# 提供额外的便捷工具函数
def get_data_dir() -> Path:
    """获取默认数据目录"""
    # 相对于项目根目录的data文件夹
    return Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"))

def ensure_data_dir() -> Path:
    """确保数据目录存在并返回路径"""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
