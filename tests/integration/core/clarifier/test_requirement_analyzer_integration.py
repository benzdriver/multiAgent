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
                "requirements": [
                    {
                        "id": "REQ-001",
                        "title": "用户认证",
                        "description": "系统应支持用户认证",
                        "priority": "高",
                        "type": "功能性"
                    },
                    {
                        "id": "REQ-002",
                        "title": "数据管理",
                        "description": "系统应支持数据管理",
                        "priority": "中",
                        "type": "功能性"
                    }
                ],
                "stakeholders": ["用户", "管理员"],
                "constraints": ["安全性", "性能"],
                "assumptions": ["用户有互联网连接"]
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
            await clarifier.clarify()
            
            mock_generate.assert_called_once()

    async def test_integration_with_file_system(self):
        """测试与文件系统的集成"""
        with open(self.doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        result = self.analyzer.analyze_requirements(content, self.mock_llm_chat)
        
        self.analyzer.generate_requirement_summary(result)
        
        summary_path = Path(self.output_dir) / "requirement_summary.md"
        self.assertTrue(summary_path.exists())
        
        with open(summary_path, "r", encoding="utf-8") as f:
            summary_content = f.read()
            self.assertIn("REQ-001", summary_content)
            self.assertIn("用户认证", summary_content)
            self.assertIn("REQ-002", summary_content)
            self.assertIn("数据管理", summary_content)

    async def test_integration_with_granular_modules(self):
        """测试细粒度模块生成与文件系统集成"""
        self.mock_llm_chat.return_value = {
            "result": json.dumps({
                "modules": [
                    {
                        "module_name": "AuthModule",
                        "layer": "business",
                        "domain": "认证",
                        "responsibilities": ["用户认证", "权限验证"],
                        "requirements": ["REQ-001"],
                        "dependencies": []
                    },
                    {
                        "module_name": "DataModule",
                        "layer": "business",
                        "domain": "数据",
                        "responsibilities": ["数据管理", "数据验证"],
                        "requirements": ["REQ-002"],
                        "dependencies": []
                    }
                ]
            })
        }
        
        with open(self.doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        result = self.analyzer.analyze_granular_modules(content, self.mock_llm_chat)
        
        auth_module_dir = Path(self.output_dir) / "modules" / "AuthModule"
        data_module_dir = Path(self.output_dir) / "modules" / "DataModule"
        self.assertTrue(auth_module_dir.exists())
        self.assertTrue(data_module_dir.exists())
        
        auth_summary_path = auth_module_dir / "full_summary.json"
        data_summary_path = data_module_dir / "full_summary.json"
        self.assertTrue(auth_summary_path.exists())
        self.assertTrue(data_summary_path.exists())
        
        with open(auth_summary_path, "r", encoding="utf-8") as f:
            auth_content = json.load(f)
            self.assertEqual(auth_content["module_name"], "AuthModule")
            self.assertEqual(auth_content["layer"], "business")
            self.assertIn("用户认证", auth_content["responsibilities"])
        
        with open(data_summary_path, "r", encoding="utf-8") as f:
            data_content = json.load(f)
            self.assertEqual(data_content["module_name"], "DataModule")
            self.assertEqual(data_content["layer"], "business")
            self.assertIn("数据管理", data_content["responsibilities"])
