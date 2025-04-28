from typing import Dict, List, Any, Optional
import asyncio
from core.validator.validator import run_validator

class ValidatorService:
    """
    Validator服务类，提供所有与Validator交互的业务逻辑
    作为Web API和Validator核心逻辑之间的中间层
    """
    
    def __init__(self):
        """初始化服务"""
        self.is_initialized = False
        
    async def initialize(self) -> Dict[str, Any]:
        """
        初始化Validator服务
        
        Returns:
            包含初始化状态的字典
        """
        if self.is_initialized:
            return {"status": "already_initialized"}
        
        try:
            self.is_initialized = True
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def validate_architecture(self, modules_to_check=None) -> Dict[str, Any]:
        """
        验证架构
        
        Args:
            modules_to_check: 可选，指定要检查的模块列表，None表示检查所有模块
            
        Returns:
            包含验证结果的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        try:
            result = await run_validator(modules_to_check)
            return {
                "status": "success", 
                "message": "架构验证完成",
                "result": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
