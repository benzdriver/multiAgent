"""
聊天API模块，提供聊天相关接口
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from services.state_service import StateService, get_state_service
from common.json_utils import parse_and_update_global_state

router = APIRouter()

class Message(BaseModel):
    content: str

@router.post("/chat")
async def chat(
    message: Message, 
    state_service: StateService = Depends(get_state_service)
) -> Dict[str, Any]:
    """处理用户聊天消息"""
    clarifier = state_service.get_clarifier()
    if clarifier is None:
        print("⚠️ Clarifier未初始化，正在初始化...")
        raise HTTPException(status_code=500, detail="Clarifier未初始化")
    
    user_message = message.content.strip()
    print(f"📝 用户消息: '{user_message}'")
    
    state_service.add_conversation_message("user", user_message)
    
    current_mode = state_service.get_current_mode()
    uploaded_files = state_service.get_uploaded_files()
    
    conversation_history = state_service.get_conversation_history()
    if len(conversation_history) >= 2:
        prev_message = conversation_history[-2]
        if prev_message["role"] == "clarifier" and "深度澄清" in prev_message["content"] and "深度推理" in prev_message["content"]:
            print(f"🔍 检测到深度分析选项提示，用户输入: '{user_message}'")
            
            if user_message == "1":
                print("📊 用户选择了深度澄清")
                state_service.add_conversation_message("system", "正在触发深度澄清...")
                try:
                    return {"status": "success", "message": "Deep clarification triggered"}
                except Exception as e:
                    print(f"❌ 深度澄清出错: {str(e)}")
                    state_service.add_conversation_message("system", f"触发深度澄清时出错: {str(e)}")
                    return {"status": "error", "message": str(e)}
            
            elif user_message == "2":
                print("🏗️ 用户选择了深度推理")
                state_service.add_conversation_message("system", "正在触发深度架构推理...")
                try: 
                    return {"status": "success", "message": "Deep reasoning triggered"}
                except Exception as e:
                    print(f"❌ 触发深度推理时出错: {str(e)}")
                    state_service.add_conversation_message("system", f"触发深度架构推理时出错: {str(e)}")
                    return {"status": "error", "message": str(e)}
    
    if current_mode is None:
        if user_message == "1":
            state_service.set_current_mode("file_based")
            state_service.add_conversation_message(
                "clarifier",
                "您选择了基于文件分析模式。请上传需求文档（.md格式）。"
            )
            return {"status": "success", "mode": "file_based"}
        elif user_message == "2":
            state_service.set_current_mode("interactive")
            state_service.add_conversation_message(
                "clarifier",
                "您选择了交互式对话模式。请描述您的业务需求，我将帮助您澄清需求并生成架构建议。"
            )
            return {"status": "success", "mode": "interactive"}
    
    if current_mode == "file_based":
        if len(uploaded_files) > 0 and user_message.upper() == "Y":
            state_service.add_conversation_message(
                "clarifier",
                "请上传需求文档（.md格式）或输入Y开始分析已上传的文档。"
            )
        else:
            state_service.add_conversation_message(
                "clarifier",
                "请上传需求文档（.md格式）或输入Y开始分析已上传的文档。"
            )
    else:
        if clarifier:
            try:
                clarifier_response = await clarifier.run_llm(
                    user_message=user_message,
                    system_message="你是一个专业的需求分析师和架构设计师，帮助用户澄清业务需求并设计合适的架构。"
                )
                
                global_state = state_service.get_global_state()
                updated_state = parse_and_update_global_state(clarifier_response, global_state)
                state_service.update_global_state(updated_state)
                
                state_service.add_conversation_message("clarifier", clarifier_response)
            except Exception as e:
                state_service.add_conversation_message("system", f"处理您的消息时出错: {str(e)}")
    
    return {"status": "success"}
