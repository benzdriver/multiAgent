"""
启动服务模块，处理应用初始化
"""

from typing import Dict, Any, List
from pathlib import Path
from services.state_service import get_state_service, StateService
from core.clarifier import create_clarifier, ensure_data_dir
from fastapi import Depends

class StartupService:
    """
    启动服务类，处理应用初始化逻辑
    """
    
    def __init__(self, state_service: StateService):
        """初始化启动服务"""
        self.state_service = state_service
    
    async def startup_event(self) -> Dict[str, Any]:
        """应用启动事件处理"""
        self.state_service.add_conversation_message("system", "系统启动中，正在初始化...")
        
        try:
            await self.initialize()
            return {"status": "success"}
        except Exception as e:
            self.state_service.add_conversation_message("system", f"系统初始化失败: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def initialize(self, use_mock: bool = False) -> Dict[str, Any]:
        """
        初始化Clarifier
        
        Args:
            use_mock: 是否使用模拟LLM响应
            
        Returns:
            包含初始化状态的字典
        """
        try:
            clarifier = create_clarifier(
                data_dir="data",
                use_mock=use_mock,
                verbose=True
            )
            
            self.state_service.set_clarifier(clarifier)
            
            input_dir = Path("data/input")
            if input_dir.exists():
                md_files = list(input_dir.glob('**/*.md'))
                txt_files = list(input_dir.glob('**/*.txt'))
                input_files = md_files + txt_files
                
                if input_files:
                    print(f"✅ 检测到 {len(input_files)} 个输入文档，开始自动分析...")
                    self.state_service.set_current_mode("file_based")
                    
                    for file_path in input_files:
                        self.state_service.add_uploaded_file(str(file_path))
                    
                    try:
                        from webui.api.document_api import analyze_documents
                        await analyze_documents(state_service=self.state_service)
                        print("✅ 文档自动分析完成")
                    except Exception as e:
                        print(f"⚠️ 文档自动分析失败: {str(e)}")
            
            print("✅ Clarifier已成功初始化")
            return {"status": "success", "message": "Clarifier initialized"}
        except Exception as e:
            print(f"❌ Clarifier初始化失败: {str(e)}")
            return {"status": "error", "message": f"Clarifier initialization failed: {str(e)}"}

def get_startup_service(state_service: StateService = Depends(get_state_service)) -> StartupService:
    """获取启动服务实例，用于依赖注入"""
    return StartupService(state_service)
