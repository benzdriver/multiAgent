"""
主应用模块，提供FastAPI应用实例和基础配置
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from typing import Dict, Any

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入API路由
from webui.api import clarifier_api, validator_api, fixer_api, generator_api

# 导入新的API路由
import webui.api.clarifier_api_new as clarifier_api_new
import webui.api.state_api as state_api
import webui.api.chat_api as chat_api
import webui.api.deep_reasoning_api as deep_reasoning_api
import webui.api.document_api as document_api

# 导入服务
from services.startup_service import get_startup_service

# 创建FastAPI应用
app = FastAPI(title="需求澄清与架构设计系统")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册现有API路由
app.include_router(clarifier_api.router, prefix="/api/clarifier", tags=["clarifier"])
app.include_router(validator_api.router, prefix="/api/validator", tags=["validator"])
app.include_router(fixer_api.router, prefix="/api/fixer", tags=["fixer"])
app.include_router(generator_api.router, prefix="/api/generator", tags=["generator"])

# 注册新的API路由
app.include_router(clarifier_api_new.router, prefix="/api", tags=["clarifier_new"])
app.include_router(state_api.router, prefix="/api", tags=["state"])
app.include_router(chat_api.router, prefix="/api", tags=["chat"])
app.include_router(deep_reasoning_api.router, prefix="/api", tags=["deep_reasoning"])
app.include_router(document_api.router, prefix="/api", tags=["document"])

# 静态文件
app.mount("/static", StaticFiles(directory="webui/static"), name="static")

# 静态文件路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页HTML"""
    with open("webui/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件，初始化系统"""
    startup_service = get_startup_service()
    await startup_service.startup_event()

# 主函数
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webui.app:app", host="0.0.0.0", port=8080, reload=True)
