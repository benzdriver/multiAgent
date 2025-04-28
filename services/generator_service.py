from typing import Dict, List, Any, Optional
import asyncio
from pathlib import Path
from core.generator.autogen_module_generator import generate_module, generate_all_modules

class GeneratorService:
    """
    Generator服务类，提供所有与Generator交互的业务逻辑
    作为Web API和Generator核心逻辑之间的中间层
    """
    
    def __init__(self):
        """初始化服务"""
        self.is_initialized = False
        
    async def initialize(self) -> Dict[str, Any]:
        """
        初始化Generator服务
        
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
    
    async def generate_code(self, module_name: str, prompt: str, output_path: str) -> Dict[str, Any]:
        """
        生成代码
        
        Args:
            module_name: 模块名称
            prompt: 生成提示
            output_path: 输出路径
            
        Returns:
            包含生成结果的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        try:
            resolved_path = Path(output_path)
            await generate_module(module_name, prompt, resolved_path)
            return {
                "status": "success", 
                "message": f"模块 {module_name} 代码生成完成",
                "output_path": str(resolved_path / f"{module_name.lower()}.ts")
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def generate_all(self) -> Dict[str, Any]:
        """
        生成所有模块代码
        
        Returns:
            包含生成结果的字典
        """
        if not self.is_initialized:
            return {"status": "error", "message": "系统尚未初始化"}
        
        try:
            await generate_all_modules()
            return {
                "status": "success", 
                "message": "所有模块代码生成完成"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
