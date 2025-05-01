"""
集成测试 - RequirementAnalyzer
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import tempfile
import shutil
import os
from pathlib import Path

from core.clarifier.requirement_analyzer import RequirementAnalyzer
from core.clarifier.clarifier import Clarifier


class TestRequirementAnalyzerIntegration(unittest.IsolatedAsyncioTestCase):
    """测试 RequirementAnalyzer 与其他模块的集成"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.doc_path = self.input_dir / "requirements.md"
        with open(self.doc_path, "w", encoding="utf-8") as f:
            f.write("# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理")
        
        self.analyzer = RequirementAnalyzer(
            output_dir=str(self.output_dir)
        )
        
        self.mock_llm_chat = AsyncMock()
        self.mock_llm_chat.return_value = {
            "result": json.dumps({
                "system_overview": {
                    "core_purpose": "测试系统",
                    "main_features": ["用户认证", "数据管理"],
                    "target_users": ["用户", "管理员"]
                },
                "functional_requirements": {
                    "core_features": [
                        {
                            "name": "用户认证",
                            "description": "系统应支持用户认证",
                            "user_stories": ["用户需要登录系统"],
                            "acceptance_criteria": ["用户可以使用用户名和密码登录"]
                        },
                        {
                            "name": "数据管理",
                            "description": "系统应支持数据管理",
                            "user_stories": ["用户需要管理数据"],
                            "acceptance_criteria": ["用户可以增删改查数据"]
                        }
                    ],
                    "secondary_features": []
                },
                "non_functional_requirements": {
                    "performance": ["系统响应时间应小于1秒"],
                    "security": ["系统应保护用户数据安全"],
                    "usability": ["系统应易于使用"],
                    "scalability": ["系统应支持扩展"]
                },
                "constraints": {
                    "technical": ["使用现代Web技术"],
                    "business": ["符合行业标准"],
                    "resources": ["开发团队有限"]
                },
                "risks": [
                    {
                        "description": "安全风险",
                        "impact": "高",
                        "probability": "中",
                        "mitigation": "实施安全措施"
                    }
                ],
                "priority": {
                    "must_have": ["用户认证"],
                    "should_have": ["数据管理"],
                    "could_have": ["报表生成"],
                    "wont_have": ["社交功能"]
                }
            })
        }

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_integration_with_clarifier(self):
        """测试与Clarifier的集成"""
        clarifier = Clarifier(
            input_path=str(self.input_dir),
            output_path=str(self.output_dir),
            llm_chat=self.mock_llm_chat
        )
        
        clarifier.document_processor = MagicMock()
        clarifier.document_processor.process_documents.return_value = "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理"
        
        clarifier.requirement_analyzer = self.analyzer
        
        with patch.object(RequirementAnalyzer, 'generate_requirement_summary') as mock_generate:
            mock_generate.return_value = asyncio.Future()
            mock_generate.return_value.set_result(None)
            await clarifier.clarify()
            
            mock_generate.assert_called_once()

    async def test_integration_with_file_system(self):
        """测试与文件系统的集成"""
        with open(self.doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.mock_llm_chat.return_value = {
            "result": json.dumps({
                "system_overview": {
                    "core_purpose": "测试系统",
                    "main_features": ["用户认证", "数据管理"],
                    "target_users": ["用户", "管理员"]
                },
                "functional_requirements": {
                    "core_features": [
                        {
                            "name": "用户认证",
                            "description": "系统应支持用户认证",
                            "user_stories": ["用户需要登录系统"],
                            "acceptance_criteria": ["用户可以使用用户名和密码登录"]
                        },
                        {
                            "name": "数据管理",
                            "description": "系统应支持数据管理",
                            "user_stories": ["用户需要管理数据"],
                            "acceptance_criteria": ["用户可以增删改查数据"]
                        }
                    ],
                    "secondary_features": []
                },
                "non_functional_requirements": {
                    "performance": ["系统响应时间应小于1秒"],
                    "security": ["系统应保护用户数据安全"],
                    "usability": ["系统应易于使用"],
                    "scalability": ["系统应支持扩展"]
                },
                "constraints": {
                    "technical": ["使用现代Web技术"],
                    "business": ["符合行业标准"],
                    "resources": ["开发团队有限"]
                }
            })
        }
        
        result = await self.analyzer.analyze_requirements(content, self.mock_llm_chat)
        
        with patch('pathlib.Path.write_text') as mock_write_text:
            await self.analyzer.generate_requirement_summary(result)
            
            mock_write_text.assert_called_once()
            
            write_call = mock_write_text.call_args[0][0]
            self.assertIn("用户认证", write_call)
            self.assertIn("数据管理", write_call)
            self.assertIn("系统应支持用户认证", write_call)
            self.assertIn("系统应支持数据管理", write_call)

    async def test_integration_with_granular_modules(self):
        """测试细粒度模块生成与文件系统集成"""
        self.mock_llm_chat.return_value = {
            "result": json.dumps([
                {
                    "module_name": "AuthModule",
                    "module_type": "Service",
                    "layer": "business",
                    "domain": "认证",
                    "responsibilities": ["用户认证", "权限验证"],
                    "requirements": ["REQ-001"],
                    "dependencies": []
                },
                {
                    "module_name": "DataModule",
                    "module_type": "Service",
                    "layer": "business",
                    "domain": "数据",
                    "responsibilities": ["数据管理", "数据验证"],
                    "requirements": ["REQ-002"],
                    "dependencies": []
                }
            ])
        }
        
        with open(self.doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        with patch.object(RequirementAnalyzer, '_save_granular_modules') as mock_save:
            result = await self.analyzer.analyze_granular_modules(content, self.mock_llm_chat)
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["module_name"], "AuthModule")
            self.assertEqual(result[1]["module_name"], "DataModule")
            
            mock_save.assert_called_once_with(result)
