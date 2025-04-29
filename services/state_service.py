"""
状态服务模块，提供全局状态管理功能
"""

from fastapi import Depends
from typing import Dict, List, Any, Optional
import os
from functools import lru_cache

class StateService:
    """状态服务类，管理全局状态"""
    
    def __init__(self):
        """初始化状态服务"""
        self.global_state: Dict[str, Any] = {
            "requirements": {},
            "modules": {},
            "technology_stack": {},
            "requirement_module_index": {},
            "architecture_pattern": {},
            "validation_issues": {},
            "circular_dependencies": []
        }
        self.conversation_history: List[Dict[str, str]] = []
        self.current_mode: Optional[str] = None
    
    def get_global_state(self) -> Dict[str, Any]:
        """获取全局状态"""
        return self.global_state
    
    def update_global_state(self, new_state: Dict[str, Any]) -> Dict[str, Any]:
        """更新全局状态"""
        self.global_state.update(new_state)
        return self.global_state
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def add_conversation_message(self, role: str, content: str) -> None:
        """添加对话消息"""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_current_mode(self) -> Optional[str]:
        """获取当前模式"""
        return self.current_mode
    
    def set_current_mode(self, mode: str) -> None:
        """设置当前模式"""
        self.current_mode = mode
    
    def add_requirement(self, requirement_id: str, requirement_data: Dict[str, Any]) -> None:
        """添加需求"""
        if "requirements" not in self.global_state:
            self.global_state["requirements"] = {}
        self.global_state["requirements"][requirement_id] = requirement_data
    
    def add_module(self, module_id: str, module_data: Dict[str, Any]) -> None:
        """添加模块"""
        if "modules" not in self.global_state:
            self.global_state["modules"] = {}
        self.global_state["modules"][module_id] = module_data
    
    def add_validation_issue(self, issue_type: str, issue_data: Dict[str, Any]) -> None:
        """添加验证问题"""
        if "validation_issues" not in self.global_state:
            self.global_state["validation_issues"] = {}
        if issue_type not in self.global_state["validation_issues"]:
            self.global_state["validation_issues"][issue_type] = []
        self.global_state["validation_issues"][issue_type].append(issue_data)
    
    def add_circular_dependency(self, dependency_data: Dict[str, Any]) -> None:
        """添加循环依赖"""
        if "circular_dependencies" not in self.global_state:
            self.global_state["circular_dependencies"] = []
        self.global_state["circular_dependencies"].append(dependency_data)
    
    def clear_global_state(self) -> None:
        """清空全局状态"""
        self.global_state = {
            "requirements": {},
            "modules": {},
            "technology_stack": {},
            "requirement_module_index": {},
            "architecture_pattern": {},
            "validation_issues": {},
            "circular_dependencies": []
        }
    
    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self.conversation_history = []

@lru_cache()
def get_state_service() -> StateService:
    """获取状态服务实例（单例模式）"""
    return StateService()
