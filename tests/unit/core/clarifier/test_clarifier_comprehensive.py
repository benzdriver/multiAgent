"""
单元测试 - Clarifier
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
import json
import tempfile
import shutil
import os
from pathlib import Path

from core.clarifier.clarifier import Clarifier
from core.clarifier.requirement_analyzer import RequirementAnalyzer
from core.clarifier.architecture_generator import ArchitectureGenerator
from core.clarifier.architecture_reasoner import ArchitectureReasoner
from core.clarifier.document_processor import DocumentProcessor


class TestClarifier(unittest.IsolatedAsyncioTestCase):
    """测试 Clarifier 类"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.input_dir = self.data_dir / "input"
        self.output_dir = self.data_dir / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.req_doc_path = self.input_dir / "requirements.md"
        with open(self.req_doc_path, "w", encoding="utf-8") as f:
            f.write("# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理")
            
        self.arch_doc_path = self.input_dir / "architecture.md"
        with open(self.arch_doc_path, "w", encoding="utf-8") as f:
            f.write("# 架构文档\n## 架构模式\n采用分层架构\n## 层级\n- 表现层\n- 业务层\n- 数据层")
        
        self.mock_llm_chat = AsyncMock()
        self.mock_llm_chat.return_value = {
            "system_overview": {
                "core_features": ["用户认证", "数据管理"],
                "key_requirements": ["安全性", "性能"],
                "technical_choices": ["分层架构", "微服务"]
            },
            "architecture_design": {
                "patterns": [
                    {
                        "name": "分层架构",
                        "description": "将系统分为多个层级",
                        "layers": [
                            {
                                "name": "表现层",
                                "responsibility": "负责用户界面",
                                "components": ["UI组件", "页面"]
                            },
                            {
                                "name": "业务层",
                                "responsibility": "负责业务逻辑",
                                "components": ["服务", "控制器"]
                            },
                            {
                                "name": "数据层",
                                "responsibility": "负责数据访问",
                                "components": ["模型", "仓储"]
                            }
                        ]
                    }
                ],
                "key_interfaces": ["用户接口", "数据接口"]
            },
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "用户认证",
                    "description": "系统应支持用户认证"
                },
                {
                    "id": "REQ-002",
                    "title": "数据管理",
                    "description": "系统应支持数据管理"
                }
            ]
        }
        
        self.clarifier = Clarifier(
            data_dir=str(self.data_dir),
            llm_chat=self.mock_llm_chat
        )

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_init(self):
        """测试初始化"""
        self.assertEqual(self.clarifier.data_dir, Path(self.data_dir))
        self.assertEqual(self.clarifier.input_dir, self.input_dir)
        self.assertEqual(self.clarifier.output_dir, self.output_dir)
        self.assertEqual(self.clarifier.llm_chat, self.mock_llm_chat)
        self.assertIsNotNone(self.clarifier.logger)
        self.assertIsNotNone(self.clarifier.requirement_analyzer)
        self.assertIsNotNone(self.clarifier.architecture_generator)
        self.assertIsNone(self.clarifier.waiting_for_user)

    async def test_start_with_input_dir_not_exists(self):
        """测试启动时输入目录不存在"""
        shutil.rmtree(self.input_dir)
        
        with patch.object(self.clarifier.logger, 'log') as mock_log:
            await self.clarifier.start()
            
            self.assertTrue(self.input_dir.exists())
            
            mock_log.assert_any_call(self.clarifier.prompts["welcome"], role="system")
            mock_log.assert_any_call(f"已创建输入文件夹：{self.input_dir}", role="system")
            mock_log.assert_any_call("请将您的需求文档放入此文件夹，然后重新启动程序。", role="system")

    async def test_start_with_file_based_mode(self):
        """测试启动文件解析模式"""
        with patch.object(self.clarifier, '_file_based_clarification') as mock_file_clarification:
            mock_file_clarification.return_value = asyncio.Future()
            mock_file_clarification.return_value.set_result(None)
            
            with patch('builtins.input', return_value="1"):
                await self.clarifier.start()
                
                mock_file_clarification.assert_called_once()

    async def test_start_with_interactive_mode(self):
        """测试启动交互式模式"""
        with patch.object(self.clarifier, '_interactive_clarification') as mock_interactive_clarification:
            mock_interactive_clarification.return_value = asyncio.Future()
            mock_interactive_clarification.return_value.set_result(None)
            
            with patch('builtins.input', return_value="2"):
                await self.clarifier.start()
                
                mock_interactive_clarification.assert_called_once()

    async def test_start_with_invalid_mode(self):
        """测试启动无效模式"""
        with patch.object(self.clarifier.logger, 'log') as mock_log:
            with patch('builtins.input', return_value="3"):
                await self.clarifier.start()
                
                mock_log.assert_any_call("无效的选项，请重新启动并选择正确的选项。", role="system")

    async def test_read_all_markdown_files(self):
        """测试读取所有Markdown文件"""
        documents = await self.clarifier._read_all_markdown_files()
        
        self.assertEqual(len(documents), 2)
        self.assertIn("requirements.md", documents)
        self.assertIn("architecture.md", documents)
        self.assertIn("# 需求文档", documents["requirements.md"])
        self.assertIn("# 架构文档", documents["architecture.md"])

    async def test_read_all_markdown_files_with_custom_path(self):
        """测试使用自定义路径读取Markdown文件"""
        custom_dir = Path(self.temp_dir) / "custom"
        custom_dir.mkdir(parents=True, exist_ok=True)
        
        custom_doc_path = custom_dir / "custom.md"
        with open(custom_doc_path, "w", encoding="utf-8") as f:
            f.write("# 自定义文档\n## 自定义标题\n自定义内容")
        
        documents = await self.clarifier._read_all_markdown_files(str(custom_dir))
        
        self.assertEqual(len(documents), 1)
        self.assertIn("custom.md", documents)
        self.assertIn("# 自定义文档", documents["custom.md"])

    async def test_run_llm(self):
        """测试运行LLM"""
        prompt = "测试提示词"
        
        with patch('core.clarifier.clarifier.run_prompt') as mock_run_prompt:
            mock_run_prompt.return_value = asyncio.Future()
            mock_run_prompt.return_value.set_result("测试响应")
            
            result = await self.clarifier.run_llm(prompt)
            
            mock_run_prompt.assert_called_once_with(
                chat=self.mock_llm_chat,
                user_message=prompt,
                model="gpt-4o",
                use_mock=False
            )
            
            self.assertEqual(result, "测试响应")

    async def test_run_llm_with_error(self):
        """测试运行LLM出错"""
        prompt = "测试提示词"
        
        with patch('core.clarifier.clarifier.run_prompt', side_effect=Exception("测试异常")):
            result = await self.clarifier.run_llm(prompt)
            
            self.assertIn("error", result)
            self.assertIn("message", result)
            self.assertIn("测试异常", result["error"])

    async def test_deep_clarification(self):
        """测试深度需求澄清"""
        requirement_analysis = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "用户认证",
                    "description": "系统应支持用户认证"
                },
                {
                    "id": "REQ-002",
                    "title": "数据管理",
                    "description": "系统应支持数据管理"
                }
            ]
        }
        
        with patch.object(self.clarifier, 'run_llm') as mock_run_llm:
            mock_run_llm.return_value = asyncio.Future()
            mock_run_llm.return_value.set_result("深度澄清结果")
            
            with patch('builtins.open', mock_open()) as mock_file:
                result = await self.clarifier.deep_clarification(requirement_analysis)
                
                mock_run_llm.assert_called_once()
                
                mock_file.assert_called_once_with(
                    self.output_dir / "deep_requirements_clarification.md",
                    "w",
                    encoding="utf-8"
                )
                
                self.assertIn("clarification_result", result)
                self.assertEqual(result["clarification_result"], "深度澄清结果")

    async def test_deep_reasoning(self):
        """测试深度架构推理"""
        requirement_analysis = {
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "用户认证",
                    "description": "系统应支持用户认证"
                },
                {
                    "id": "REQ-002",
                    "title": "数据管理",
                    "description": "系统应支持数据管理"
                }
            ]
        }
        
        architecture_analysis = {
            "architecture_pattern": {
                "name": "分层架构",
                "description": "将系统分为多个层级"
            },
            "modules": [
                {
                    "name": "认证模块",
                    "description": "处理用户认证"
                },
                {
                    "name": "数据模块",
                    "description": "管理数据"
                }
            ],
            "technology_stack": [
                "Spring Boot",
                "React",
                "PostgreSQL"
            ]
        }
        
        with patch.object(self.clarifier, 'run_llm') as mock_run_llm:
            mock_run_llm.return_value = asyncio.Future()
            mock_run_llm.return_value.set_result("深度推理结果")
            
            with patch('builtins.open', mock_open()) as mock_file:
                result = await self.clarifier.deep_reasoning(requirement_analysis, architecture_analysis)
                
                mock_run_llm.assert_called_once()
                
                mock_file.assert_called_once_with(
                    self.output_dir / "deep_architecture_reasoning.md",
                    "w",
                    encoding="utf-8"
                )
                
                self.assertIn("reasoning_result", result)
                self.assertEqual(result["reasoning_result"], "深度推理结果")

    async def test_integrate_legacy_modules(self):
        """测试集成legacy模块"""
        modules_dir = self.output_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        
        module_dir = modules_dir / "TestModule"
        module_dir.mkdir(parents=True, exist_ok=True)
        
        module_data = {
            "module_name": "TestModule",
            "layer": "表现层",
            "domain": "UI",
            "responsibilities": ["测试责任1", "测试责任2"],
            "requirements": ["REQ-001", "REQ-002"],
            "dependencies": ["TestDep1", "TestDep2"]
        }
        
        with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(module_data, f, ensure_ascii=False, indent=2)
        
        with patch('core.clarifier.architecture_manager.ArchitectureManager.process_new_module') as mock_process:
            mock_process.return_value = asyncio.Future()
            mock_process.return_value.set_result(None)
            
            with patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._check_global_circular_dependencies') as mock_check:
                mock_check.return_value = []
                
                result = await self.clarifier.integrate_legacy_modules(
                    input_path=str(self.input_dir),
                    output_path=str(self.output_dir)
                )
                
                mock_process.assert_called_once()
                
                mock_check.assert_called_once()
                
                self.assertIn("modules_count", result)
                self.assertIn("circular_dependencies", result)
                self.assertEqual(result["modules_count"], 1)
                self.assertEqual(result["circular_dependencies"], [])

    async def test_generate_granular_modules(self):
        """测试生成细粒度模块"""
        with patch.object(self.clarifier, '_read_all_markdown_files') as mock_read:
            mock_read.return_value = asyncio.Future()
            mock_read.return_value.set_result({
                "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理",
                "architecture.md": "# 架构文档\n## 架构模式\n采用分层架构\n## 层级\n- 表现层\n- 业务层\n- 数据层"
            })
            
            with patch.object(RequirementAnalyzer, 'analyze_granular_modules') as mock_analyze:
                mock_analyze.return_value = asyncio.Future()
                mock_analyze.return_value.set_result([
                    {
                        "module_name": "登录页面",
                        "layer": "表现层",
                        "type": "页面",
                        "description": "用户登录界面",
                        "requirements": ["REQ-001"]
                    },
                    {
                        "module_name": "认证服务",
                        "layer": "业务层",
                        "type": "服务",
                        "description": "处理用户认证逻辑",
                        "requirements": ["REQ-001"]
                    },
                    {
                        "module_name": "用户仓储",
                        "layer": "数据层",
                        "type": "仓储",
                        "description": "管理用户数据",
                        "requirements": ["REQ-002"]
                    }
                ])
                
                with patch('core.clarifier.architecture_manager.ArchitectureManager.process_new_module') as mock_process:
                    mock_process.return_value = asyncio.Future()
                    mock_process.return_value.set_result(None)
                    
                    with patch('core.clarifier.index_generator.MultiDimensionalIndexGenerator.generate_indices') as mock_generate:
                        mock_generate.return_value = {
                            "layer_index": {},
                            "domain_index": {},
                            "responsibility_index": {},
                            "requirement_module_index": {},
                            "cross_cutting_index": {}
                        }
                        
                        with patch.object(ArchitectureReasoner, 'check_all_issues') as mock_check:
                            mock_check.return_value = asyncio.Future()
                            mock_check.return_value.set_result({})
                            
                            result = await self.clarifier.generate_granular_modules(
                                input_path=str(self.input_dir),
                                output_path=str(self.output_dir)
                            )
                            
                            mock_read.assert_called_once_with(str(self.input_dir))
                            
                            mock_analyze.assert_called_once()
                            
                            self.assertEqual(mock_process.call_count, 3)
                            
                            mock_generate.assert_called_once()
                            
                            mock_check.assert_called_once()
                            
                            self.assertIn("modules_count", result)
                            self.assertIn("issues_count", result)
                            self.assertEqual(result["modules_count"], 3)
                            self.assertEqual(result["issues_count"], 0)

    async def test_continue_from_user(self):
        """测试从用户继续"""
        self.clarifier.waiting_for_user = asyncio.Event()
        
        self.assertFalse(self.clarifier.waiting_for_user.is_set())
        
        self.clarifier.continue_from_user()
        
        self.assertTrue(self.clarifier.waiting_for_user.is_set())
