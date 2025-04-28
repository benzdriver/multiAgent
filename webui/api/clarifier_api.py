from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, List, Any, Optional
from services.clarifier_service import ClarifierService

router = APIRouter()
clarifier_service = ClarifierService()

@router.post("/initialize")
async def initialize(use_mock: bool = False) -> Dict[str, Any]:
    """初始化Clarifier服务"""
    return await clarifier_service.initialize(use_mock=use_mock)

@router.post("/set_mode")
async def set_mode(mode: str) -> Dict[str, Any]:
    """设置操作模式"""
    return await clarifier_service.set_mode(mode)

@router.post("/upload_file")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """上传文件"""
    file_content = await file.read()
    return await clarifier_service.upload_file(file_content, file.filename)

@router.post("/analyze_documents")
async def analyze_documents() -> Dict[str, Any]:
    """分析文档"""
    return await clarifier_service.analyze_documents()

@router.post("/analyze_architecture")
async def analyze_architecture() -> Dict[str, Any]:
    """分析架构"""
    return await clarifier_service.analyze_architecture()

@router.post("/process_message")
async def process_message(message: str = Form(...)) -> Dict[str, Any]:
    """处理消息"""
    response = await clarifier_service.process_message(message)
    clarifier_service.add_user_message(message)
    clarifier_service.add_clarifier_message(response)
    return {"response": response}

@router.get("/conversation_history")
async def get_conversation_history() -> Dict[str, Any]:
    """获取对话历史"""
    return {"history": clarifier_service.get_conversation_history()}

@router.get("/state")
async def get_state() -> Dict[str, Any]:
    """获取状态"""
    return clarifier_service.get_state()
