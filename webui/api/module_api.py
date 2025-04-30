"""
模块API，提供模块相关接口
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import os

router = APIRouter()

@router.get("/module_summary/{module_name}")
async def get_module_summary(module_name: str):
    """获取模块摘要信息"""
    try:
        module_dir = Path(f"data/output/modules/{module_name}")
        if not module_dir.exists():
            raise HTTPException(status_code=404, detail=f"模块目录不存在: {module_name}")
        
        summary_file = module_dir / "full_summary.json"
        if not summary_file.exists():
            raise HTTPException(status_code=404, detail=f"模块摘要文件不存在: {module_name}")
        
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
        
        return summary_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模块摘要失败: {str(e)}")
