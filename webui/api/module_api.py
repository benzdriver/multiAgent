"""
模块API，提供模块相关接口
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import os
import traceback

router = APIRouter()

@router.get("/module_summary/{module_name}")
async def get_module_summary(module_name: str):
    """获取模块摘要信息"""
    try:
        module_dir = Path(f"data/output/modules/{module_name}")
        
        if not module_dir.exists():
            print(f"⚠️ 模块目录不存在: {module_name}，尝试查找匹配项")
            modules_dir = Path("data/output/modules")
            if modules_dir.exists():
                all_modules = [d.name for d in modules_dir.iterdir() if d.is_dir()]
                print(f"现有模块目录: {all_modules}")
                
                for dir_name in all_modules:
                    if dir_name.lower() == module_name.lower() or module_name in dir_name or dir_name in module_name:
                        print(f"找到可能匹配的模块目录: {dir_name}")
                        module_dir = modules_dir / dir_name
                        break
        
        if not module_dir.exists():
            print(f"❌ 无法找到模块目录: {module_name}")
            raise HTTPException(status_code=404, detail=f"模块目录不存在: {module_name}")
        
        summary_file = module_dir / "full_summary.json"
        if not summary_file.exists():
            print(f"❌ 模块摘要文件不存在: {module_dir}/full_summary.json")
            
            json_files = list(module_dir.glob("*.json"))
            if json_files:
                summary_file = json_files[0]
                print(f"✅ 找到替代摘要文件: {summary_file}")
            else:
                print(f"⚠️ 创建默认摘要文件")
                default_summary = {
                    "name": module_name,
                    "description": f"{module_name}模块",
                    "responsibilities": [f"负责{module_name}相关功能"],
                    "dependencies": [],
                    "layer": "未指定",
                    "domain": "未指定"
                }
                with open(summary_file, "w", encoding="utf-8") as f:
                    json.dump(default_summary, f, ensure_ascii=False, indent=2)
        
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
        
        print(f"✅ 成功获取模块 '{module_name}' 的摘要数据")
        return summary_data
    except Exception as e:
        error_msg = f"获取模块摘要失败: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)
