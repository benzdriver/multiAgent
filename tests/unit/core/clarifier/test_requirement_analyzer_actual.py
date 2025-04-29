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

    async def test_analyze_requirements(self):
        """测试分析需求文档"""
        mock_json_data = {
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
        
        mock_response = {
            "result": json.dumps(mock_json_data)
        }
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            return mock_response
            
        result = await self.analyzer.analyze_requirements(content, mock_llm_call)
        
        self.assertEqual(result, mock_response)

    async def test_analyze_requirements_json_error(self):
        """测试分析需求文档 - JSON解析错误"""
        mock_response = {
            "result": "这不是有效的JSON"
        }
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            return mock_response
            
        result = await self.analyzer.analyze_requirements(content, mock_llm_call)
        
        self.assertEqual(result, mock_response)

    async def test_analyze_requirements_llm_error(self):
        """测试分析需求文档 - LLM调用错误"""
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            raise Exception("LLM调用失败")
            
        result = await self.analyzer.analyze_requirements(content, mock_llm_call)
        
        self.assertIn("error", result)

    @patch('pathlib.Path.write_text')
    async def test_generate_requirement_summary_simple(self, mock_write_text):
        """测试生成简单需求摘要"""
        requirement_analysis = {
            "system_overview": {
                "core_purpose": "测试系统",
                "main_features": ["功能1", "功能2"],
                "target_users": ["用户1", "用户2"]
            },
            "functional_requirements": {
                "core_features": [
                    {
                        "name": "用户认证",
                        "description": "系统应支持用户认证",
                        "user_stories": ["故事1"],
                        "acceptance_criteria": ["标准1"]
                    }
                ],
                "secondary_features": []
            },
            "non_functional_requirements": {
                "performance": ["性能要求1"],
                "security": ["安全要求1"],
                "usability": ["可用性要求1"],
                "scalability": ["可扩展性要求1"]
            },
            "constraints": {
                "technical": ["技术约束1"],
                "business": ["业务约束1"],
                "resources": ["资源约束1"]
            },
            "risks": [
                {
                    "description": "风险1",
                    "impact": "高",
                    "probability": "中",
                    "mitigation": "缓解策略1"
                }
            ],
            "priority": {
                "must_have": ["必要功能1"],
                "should_have": ["重要功能1"],
                "could_have": ["可选功能1"]
            }
        }
        
        await self.analyzer.generate_requirement_summary(requirement_analysis)
        
        mock_write_text.assert_called_once()
        
        write_call = mock_write_text.call_args[0][0]
        self.assertIn("测试系统", write_call)
        self.assertIn("功能1", write_call)
        self.assertIn("用户认证", write_call)
        self.assertIn("系统应支持用户认证", write_call)
        self.assertIn("性能要求1", write_call)
        self.assertIn("安全要求1", write_call)

    @patch('pathlib.Path.write_text')
    async def test_generate_requirement_summary_with_llm(self, mock_write_text):
        """测试使用LLM生成需求摘要"""
        mock_llm_response = "# 需求摘要\n## 用户认证\n系统应支持用户认证，优先级高"
        
        requirement_analysis = {
            "system_overview": {
                "core_purpose": "测试系统",
                "main_features": ["功能1", "功能2"],
                "target_users": ["用户1", "用户2"]
            },
            "functional_requirements": {
                "core_features": [
                    {
                        "name": "用户认证",
                        "description": "系统应支持用户认证",
                        "user_stories": ["故事1"],
                        "acceptance_criteria": ["标准1"]
                    }
                ],
                "secondary_features": []
            },
            "non_functional_requirements": {
                "performance": ["性能要求1"],
                "security": ["安全要求1"],
                "usability": ["可用性要求1"],
                "scalability": ["可扩展性要求1"]
            },
            "constraints": {
                "technical": ["技术约束1"],
                "business": ["业务约束1"],
                "resources": ["资源约束1"]
            }
        }
        
        async def mock_llm_call(prompt):
            return mock_llm_response
            
        await self.analyzer.generate_requirement_summary(requirement_analysis, mock_llm_call)
        
        mock_write_text.assert_called_once()
        mock_write_text.assert_called_once_with(mock_llm_response, encoding="utf-8")

    async def test_analyze_granular_modules(self):
        """测试分析细粒度模块"""
        mock_modules = [
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
        
        mock_response = {
            "result": json.dumps(mock_modules)
        }
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            return mock_response
            
        with patch.object(RequirementAnalyzer, '_save_granular_modules') as mock_save:
            mock_save.return_value = None
            
            with patch('json.loads', side_effect=lambda x: []):
                result = await self.analyzer.analyze_granular_modules(content, mock_llm_call)
                
                self.assertEqual(result, [])
                
                mock_save.assert_called_once_with([])

    async def test_analyze_granular_modules_json_error(self):
        """测试分析细粒度模块 - JSON解析错误"""
        mock_response = {
            "result": "这不是有效的JSON"
        }
        
        content = "# 需求文档\n## 用户认证\n系统应支持用户认证"
        
        async def mock_llm_call(prompt, parse_response=None):
            return mock_response
            
        with patch.object(RequirementAnalyzer, '_save_granular_modules') as mock_save:
            mock_save.return_value = None
            
            result = await self.analyzer.analyze_granular_modules(content, mock_llm_call)
            
            self.assertEqual(result, [])
            
            mock_save.assert_called_once_with([])

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    async def test_save_granular_modules(self, mock_json_dump, mock_file, mock_mkdir):
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
        
        self.assertTrue(mock_mkdir.call_count >= 1)
        
        self.assertTrue(mock_file.call_count >= 1)
        self.assertTrue(mock_json_dump.call_count >= 1)
