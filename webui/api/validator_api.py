from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from services.validator_service import ValidatorService

router = APIRouter()
validator_service = ValidatorService()

@router.post("/initialize")
async def initialize() -> Dict[str, Any]:
    """初始化Validator服务"""
    return await validator_service.initialize()

@router.post("/validate")
async def validate(modules: Optional[List[str]] = None) -> Dict[str, Any]:
    """验证架构"""
    return await validator_service.validate_architecture(modules)
