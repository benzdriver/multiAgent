from typing import Dict, List, Any, Optional
import asyncio
from core.fixer.fixer import fix_all
from core.fixer.structure_fixer import fix_modules
from core.fixer.structure_loop import run_fix_loop

class FixerService:
    """
    Fixer服务类，提供所有与Fixer交互的业务逻辑
    作为Web API和Fixer核心逻辑之间的中间层
    """
    
    def __init__(self):
        """初始化服务"""
        self.is_initialized = False
        
    async def initialize(self) -> Dict[str, Any]:
        """
        初始化Fixer服务
        
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
    
    async def fix_missing_modules(self) -> Dict[str, Any]:
        """
        修复缺失的模块
        
        Returns:
            包含修复结果的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        try:
            result = await fix_all()
            return {
                "status": "success", 
                "message": "缺失模块修复完成",
                "result": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def fix_structure(self) -> Dict[str, Any]:
        """
        修复结构问题
        
        Returns:
            包含修复结果的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        try:
            result = await fix_modules()
            return {
                "status": "success", 
                "message": "结构修复完成",
                "result": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def run_fix_loop(self) -> Dict[str, Any]:
        """
        运行修复循环
        
        Returns:
            包含修复结果的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        try:
            result = await run_fix_loop()
            return {
                "status": "success", 
                "message": "修复循环完成",
                "result": result
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
