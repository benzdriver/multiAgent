"""
日志模块
提供统一的日志记录功能
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

class Logger:
    """
    通用日志记录器，支持控制台和文件输出
    """
    
    def __init__(self, name: str = "app", level: int = logging.INFO):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        self.name = name
        self.logs = []
        
        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 如果没有handler，添加控制台handler
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # 添加文件handler
            log_dir = Path("data/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_dir / f"{name}.log")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log(self, message: str, level: str = "info", role: str = "system") -> None:
        """
        记录日志消息
        
        Args:
            message: 日志消息
            level: 日志级别
            role: 消息角色
        """
        # 将消息添加到内存日志
        self.logs.append({
            "role": role,
            "content": message,
            "level": level
        })
        
        # 记录到logger
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)
        
        # 如果是system、clarifier或user角色的消息，打印到控制台
        if role in ["system", "clarifier", "user"]:
            prefix = {
                "system": "🔧 ",
                "clarifier": "🤖 ",
                "user": "👤 "
            }.get(role, "")
            print(f"{prefix}{message}")
    
    def get_logs(self, role: Optional[str] = None) -> List[Dict[str, str]]:
        """
        获取日志记录
        
        Args:
            role: 过滤的角色
            
        Returns:
            日志记录列表
        """
        if role:
            return [log for log in self.logs if log["role"] == role]
        return self.logs 