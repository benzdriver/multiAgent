"""
单元测试 - RequirementAnalyzer
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
import json
import tempfile
import shutil
import os
from pathlib import Path

from core.clarifier.requirement_analyzer import RequirementAnalyzer


class TestRequirementAnalyzer(unittest.IsolatedAsyncioTestCase):
    """测试 RequirementAnalyzer 类"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = RequirementAnalyzer(
            output_dir=str(self.output_dir)
        )

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_init(self):
        """测试初始化"""
        self.assertEqual(str(self.analyzer.output_dir), str(self.output_dir))
        self.assertIsNone(self.analyzer.logger)

    @patch('core.clarifier.requirement_analyzer.run_prompt')
    async def test_analyze_requirements(self, mock_run_prompt):
        """测试分析需求文档"""
        mock_response = {
            "result": json.dumps({
                "requirements": [
                    {
                        "id": "REQ-001",
                        "title": "用户认证",
                        "description": "系统应支持用户认证",
                        "priority": "高",
                        "type": "功能性"
                    }
                ],
                "stakeholders": ["用户", "管理员"],
                "constraints": ["安全性", "性能"],
                "assumptions": ["用户有互联网连接"]
            })
        }
        mock_run_prompt.return_value = mock_response
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            return mock_response
            
        result = await self.analyzer.analyze_requirements(content, mock_llm_call)
        
        self.assertIn("requirements", result)
        self.assertEqual(len(result["requirements"]), 1)
        self.assertEqual(result["requirements"][0]["id"], "REQ-001")
        self.assertEqual(result["requirements"][0]["title"], "用户认证")
        self.assertIn("stakeholders", result)
        self.assertIn("constraints", result)
        self.assertIn("assumptions", result)

    @patch('core.clarifier.requirement_analyzer.run_prompt')
    async def test_analyze_requirements_json_error(self, mock_run_prompt):
        """测试分析需求文档 - JSON解析错误"""
        mock_response = {
            "result": "这不是有效的JSON"
        }
        mock_run_prompt.return_value = mock_response
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            return mock_response
            
        result = await self.analyzer.analyze_requirements(content, mock_llm_call)
        
        self.assertIn("error", result)

    @patch('core.clarifier.requirement_analyzer.run_prompt')
    async def test_analyze_requirements_llm_error(self, mock_run_prompt):
        """测试分析需求文档 - LLM调用错误"""
        mock_run_prompt.side_effect = Exception("LLM调用失败")
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            raise Exception("LLM调用失败")
            
        result = await self.analyzer.analyze_requirements(content, mock_llm_call)
        
        self.assertIn("error", result)

    @patch('pathlib.Path.write_text')
    async def test_generate_requirement_summary_simple(self, mock_write_text):
        """测试生成简单需求摘要"""
        requirement_analysis = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "用户认证",
                    "description": "系统应支持用户认证",
                    "priority": "高",
                    "type": "功能性"
                }
            ],
            "stakeholders": ["用户", "管理员"],
            "constraints": ["安全性", "性能"],
            "assumptions": ["用户有互联网连接"]
        }
        
        await self.analyzer.generate_requirement_summary(requirement_analysis)
        
        mock_write_text.assert_called_once()
        
        write_call = mock_write_text.call_args[0][0]
        self.assertIn("REQ-001", write_call)
        self.assertIn("用户认证", write_call)
        self.assertIn("系统应支持用户认证", write_call)
        self.assertIn("用户", write_call)
        self.assertIn("管理员", write_call)
        self.assertIn("安全性", write_call)
        self.assertIn("性能", write_call)

    @patch('pathlib.Path.write_text')
    async def test_generate_requirement_summary_with_llm(self, mock_write_text):
        """测试使用LLM生成需求摘要"""
        mock_response = {
            "result": "# 需求摘要\n## 用户认证\n系统应支持用户认证，优先级高"
        }
        
        requirement_analysis = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "用户认证",
                    "description": "系统应支持用户认证",
                    "priority": "高",
                    "type": "功能性"
                }
            ],
            "stakeholders": ["用户", "管理员"],
            "constraints": ["安全性", "性能"],
            "assumptions": ["用户有互联网连接"]
        }
        
        async def mock_llm_call(prompt):
            return mock_response
            
        await self.analyzer.generate_requirement_summary(requirement_analysis, mock_llm_call)
        
        mock_write_text.assert_called_once()
        mock_write_text.assert_called_once_with(mock_response["result"], encoding="utf-8")

    @patch('core.clarifier.requirement_analyzer.run_prompt')
    async def test_analyze_granular_modules(self, mock_run_prompt):
        """测试分析细粒度模块"""
        mock_response = {
            "result": json.dumps([
                {
                    "module_name": "AuthModule",
                    "module_type": "Service",
                    "layer": "business",
                    "domain": "认证",
                    "responsibilities": ["用户认证", "权限验证"],
                    "requirements": ["REQ-001"],
                    "dependencies": []
                }
            ])
        }
        mock_run_prompt.return_value = mock_response
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            return mock_response
            
        with patch.object(RequirementAnalyzer, '_save_granular_modules') as mock_save:
            result = await self.analyzer.analyze_granular_modules(content, mock_llm_call)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["module_name"], "AuthModule")
            self.assertEqual(result[0]["layer"], "business")
            
            mock_save.assert_called_once_with(result)

    @patch('core.clarifier.requirement_analyzer.run_prompt')
    async def test_analyze_granular_modules_json_error(self, mock_run_prompt):
        """测试分析细粒度模块 - JSON解析错误"""
        mock_response = {
            "result": "这不是有效的JSON"
        }
        mock_run_prompt.return_value = mock_response
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            return mock_response
            
        result = await self.analyzer.analyze_granular_modules(content, mock_llm_call)
        
        self.assertEqual(result, [])

    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    async def test_save_granular_modules(self, mock_file, mock_json_dump):
        """测试保存细粒度模块"""
        modules = [
            {
                "module_name": "AuthModule",
                "module_type": "Service",
                "layer": "business",
                "domain": "认证",
                "responsibilities": ["用户认证", "权限验证"],
                "requirements": ["REQ-001"],
                "dependencies": []
            }
        ]
        
        self.analyzer._save_granular_modules(modules)
        
        self.assertTrue(mock_file.call_count >= 1)
        self.assertTrue(mock_json_dump.call_count >= 1)
        
        mock_json_dump.assert_called()
