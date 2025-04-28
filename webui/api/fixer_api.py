from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from services.fixer_service import FixerService

router = APIRouter()
fixer_service = FixerService()

@router.post("/initialize")
async def initialize() -> Dict[str, Any]:
    """初始化Fixer服务"""
    return await fixer_service.initialize()

@router.post("/fix_missing_modules")
async def fix_missing_modules() -> Dict[str, Any]:
    """修复缺失的模块"""
    return await fixer_service.fix_missing_modules()

@router.post("/fix_structure")
async def fix_structure() -> Dict[str, Any]:
    """修复结构问题"""
    return await fixer_service.fix_structure()

@router.post("/run_fix_loop")
async def run_fix_loop() -> Dict[str, Any]:
    """运行修复循环"""
    return await fixer_service.run_fix_loop()
