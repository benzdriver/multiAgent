from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from services.generator_service import GeneratorService

router = APIRouter()
generator_service = GeneratorService()

@router.post("/initialize")
async def initialize() -> Dict[str, Any]:
    """初始化Generator服务"""
    return await generator_service.initialize()

@router.post("/generate")
async def generate(module_name: str, prompt: str, output_path: str) -> Dict[str, Any]:
    """生成代码"""
    return await generator_service.generate_code(module_name, prompt, output_path)

@router.post("/generate_all")
async def generate_all() -> Dict[str, Any]:
    """生成所有模块代码"""
    return await generator_service.generate_all()
