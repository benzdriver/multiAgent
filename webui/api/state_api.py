"""
状态API模块，提供获取全局状态的接口
"""

from fastapi import APIRouter, Depends
from typing import Dict, List, Any
from services.state_service import StateService, get_state_service

router = APIRouter()

@router.get("/state")
async def get_state(state_service: StateService = Depends(get_state_service)) -> Dict[str, Any]:
    """获取全局状态"""
    return state_service.get_global_state()

@router.get("/history")
async def get_history(state_service: StateService = Depends(get_state_service)) -> List[Dict[str, str]]:
    """获取对话历史"""
    return state_service.get_conversation_history()

@router.get("/mode")
async def get_mode(state_service: StateService = Depends(get_state_service)) -> Dict[str, Any]:
    """获取当前模式"""
    return {"mode": state_service.get_current_mode()}
