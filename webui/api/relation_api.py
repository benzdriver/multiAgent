"""
关系API模块，提供获取模块和需求之间关系的接口
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any
from services.state_service import StateService, get_state_service

router = APIRouter()

@router.get("/get_related_modules/{requirement_id}")
async def get_related_modules(requirement_id: str, state_service: StateService = Depends(get_state_service)) -> Dict[str, Any]:
    """获取与需求相关的模块"""
    global_state = state_service.get_global_state()
    req_module_index = global_state.get("requirement_module_index", {})
    
    if requirement_id not in req_module_index:
        raise HTTPException(status_code=404, detail=f"需求ID不存在: {requirement_id}")
    
    module_ids = req_module_index.get(requirement_id, [])
    modules = []
    
    for module_id in module_ids:
        module_data = global_state.get("modules", {}).get(module_id)
        if module_data:
            modules.append({
                "id": module_id,
                "name": module_data.get("name", ""),
                "description": module_data.get("description", ""),
                "responsibilities": module_data.get("responsibilities", []),
                "dependencies": module_data.get("dependencies", []),
                "layer": module_data.get("layer", ""),
                "domain": module_data.get("domain", "")
            })
    
    return {"modules": modules}

@router.get("/get_related_requirements/{module_id}")
async def get_related_requirements(module_id: str, state_service: StateService = Depends(get_state_service)) -> Dict[str, Any]:
    """获取与模块相关的需求"""
    global_state = state_service.get_global_state()
    req_module_index = global_state.get("requirement_module_index", {})
    
    if module_id not in global_state.get("modules", {}):
        raise HTTPException(status_code=404, detail=f"模块ID不存在: {module_id}")
    
    requirements = []
    
    for req_id, module_ids in req_module_index.items():
        if module_id in module_ids:
            req_data = global_state.get("requirements", {}).get(req_id)
            if req_data:
                requirements.append({
                    "id": req_id,
                    "name": req_data.get("name", ""),
                    "description": req_data.get("description", ""),
                    "priority": req_data.get("priority", "中"),
                    "status": req_data.get("status", "待处理")
                })
    
    return {"requirements": requirements}
