"""
主应用模块，提供FastAPI应用实例和基础配置
"""

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles  # Still needed for frontend assets
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from typing import Dict, Any, List, Optional
from enum import Enum
from pathlib import Path
import json
import time
import asyncio
from pydantic import BaseModel

# 导入API路由
from webui.api.state_api import router as state_router
from webui.api.chat_api import router as chat_router
from webui.api.document_api import router as document_router
from webui.api.deep_reasoning_api import router as deep_reasoning_router
from webui.api.clarifier_api_new import router as clarifier_router
from webui.api.module_api import router as module_router
from webui.api.relation_api import router as relation_router

# 导入服务
from services.state_service import StateService, get_state_service

# 创建FastAPI应用
app = FastAPI(title="需求澄清与架构设计系统")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(state_router, prefix="/api", tags=["状态管理"])
app.include_router(chat_router, prefix="/api", tags=["聊天"])
app.include_router(document_router, prefix="/api", tags=["文档"])
app.include_router(deep_reasoning_router, prefix="/api", tags=["深度推理"])
app.include_router(clarifier_router, prefix="/api", tags=["澄清器"])
app.include_router(module_router, prefix="/api", tags=["模块"])
app.include_router(relation_router, prefix="/api", tags=["关系"])

# 静态文件
app.mount("/assets", StaticFiles(directory="webui/frontend/dist/assets"), name="frontend_assets")


# 静态文件路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页HTML"""
    print("🔍 提供React前端: webui/frontend/dist/index.html")
    return FileResponse("webui/frontend/dist/index.html")


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作"""
    print("应用已启动")
    
    state_service = get_state_service()
    
    from services.clarifier_service import ClarifierService
    clarifier_service = ClarifierService()
    await clarifier_service.initialize(use_mock=False)
    state_service.set_clarifier(clarifier_service.clarifier)
    print("✅ 澄清器服务已初始化，使用真实LLM响应")
    
    state_service.set_current_mode("file_based")
    print("✅ 已设置为文件模式，自动扫描data/input目录")
    
    full_analysis_path = Path("data/output/full_analysis.json")
    if full_analysis_path.exists():
        try:
            with open(full_analysis_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
                await state_service.update_global_state_from_json(json_data)
                
                req_count = len(json_data.get('requirements', {}))
                module_count = len(json_data.get('modules', {}))
                state_service.add_conversation_message(
                    "system",
                    f"已加载现有分析结果: {req_count}个需求, {module_count}个模块"
                )
        except Exception as e:
            print(f"❌ 加载分析结果失败: {str(e)}")
    
    

# 主函数
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webui.app:app", host="0.0.0.0", port=8080, reload=True)                                                                                                                                                                                                                                          