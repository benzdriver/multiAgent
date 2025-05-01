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
            "functional_requirements": {
                "user_auth": {
                    "description": "用户认证功能",
                    "priority": "高"
                },
                "data_management": {
                    "description": "数据管理功能",
                    "priority": "高"
                }
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
        
        self.mock_requirement_analyzer = MagicMock()
        self.mock_architecture_generator = MagicMock()
        
        self.clarifier.requirement_analyzer = self.mock_requirement_analyzer
        self.clarifier.architecture_generator = self.mock_architecture_generator

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_init(self):
        """测试初始化"""
        with patch('pathlib.Path.mkdir'):
            default_clarifier = Clarifier()
            self.assertEqual(default_clarifier.data_dir, Path("data"))
            self.assertEqual(default_clarifier.input_dir, Path("data/input"))
            self.assertEqual(default_clarifier.output_dir, Path("data/output"))
            self.assertIsNone(default_clarifier.llm_chat)
        
        custom_data_dir = Path(tempfile.mkdtemp()) / "custom_data"
        mock_llm = AsyncMock()
        
        with patch('pathlib.Path.mkdir'):
            custom_clarifier = Clarifier(
                data_dir=str(custom_data_dir),
                llm_chat=mock_llm
            )
            
            self.assertEqual(custom_clarifier.data_dir, custom_data_dir)
            self.assertEqual(custom_clarifier.input_dir, custom_data_dir / "input")
            self.assertEqual(custom_clarifier.output_dir, custom_data_dir / "output")
            self.assertEqual(custom_clarifier.llm_chat, mock_llm)
        
        shutil.rmtree(custom_data_dir.parent)

    @patch('builtins.input', return_value="1")
    async def test_start_file_mode(self, mock_input):
        """测试启动 - 文件模式"""
        with patch.object(Clarifier, '_file_based_clarification') as mock_file_clarification:
            mock_file_clarification.return_value = asyncio.Future()
            mock_file_clarification.return_value.set_result(None)
            
            await self.clarifier.start()
            
            mock_input.assert_called_once()
            mock_file_clarification.assert_called_once()

    @patch('builtins.input', return_value="2")
    async def test_start_interactive_mode(self, mock_input):
        """测试启动 - 交互模式"""
        with patch.object(Clarifier, '_interactive_clarification') as mock_interactive_clarification:
            mock_interactive_clarification.return_value = asyncio.Future()
            mock_interactive_clarification.return_value.set_result(None)
            
            await self.clarifier.start()
            
            mock_input.assert_called_once()
            mock_interactive_clarification.assert_called_once()

    @patch('builtins.input', return_value="3")
    async def test_start_invalid_choice(self, mock_input):
        """测试启动 - 无效选择"""
        with patch.object(self.clarifier.logger, 'log') as mock_log:
            await self.clarifier.start()
            
            mock_input.assert_called_once()
            mock_log.assert_any_call("无效的选项，请重新启动并选择正确的选项。", role="system")

    async def test_read_all_markdown_files(self):
        """测试读取所有Markdown文件"""
        documents = await self.clarifier._read_all_markdown_files()
        
        self.assertEqual(len(documents), 2)
        self.assertIn("requirements.md", documents)
        self.assertIn("architecture.md", documents)
        self.assertIn("# 需求文档", documents["requirements.md"])
        self.assertIn("# 架构文档", documents["architecture.md"])

    @patch('builtins.input', return_value="y")
    async def test_file_based_clarification_empty_dir(self, mock_input):
        """测试基于文件的澄清 - 空目录"""
        empty_dir = Path(tempfile.mkdtemp())
        empty_data_dir = empty_dir / "data"
        empty_data_dir.mkdir(parents=True, exist_ok=True)
        
        empty_input_dir = empty_data_dir / "input"
        empty_output_dir = empty_data_dir / "output"
        empty_input_dir.mkdir(parents=True, exist_ok=True)
        empty_output_dir.mkdir(parents=True, exist_ok=True)
        
        clarifier = Clarifier(
            data_dir=str(empty_data_dir),
            llm_chat=self.mock_llm_chat
        )
        
        with patch.object(clarifier, '_read_all_markdown_files') as mock_read:
            mock_read.return_value = {}  # 直接返回空字典，而不是Future
            
            with patch.object(clarifier, '_interactive_clarification') as mock_interactive:
                mock_interactive.return_value = asyncio.Future()
                mock_interactive.return_value.set_result(None)
                
                await clarifier._file_based_clarification()
                
                mock_read.assert_called_once()
                mock_input.assert_called_once()
                mock_interactive.assert_called_once()
        
        shutil.rmtree(empty_dir)

    @patch('core.llm.llm_executor.run_prompt')
    async def test_run_llm(self, mock_run_prompt):
        """测试运行LLM"""
        result = await self.clarifier.run_llm("测试提示")
        
        self.mock_llm_chat.assert_called_once()
        self.assertEqual(result, self.mock_llm_chat.return_value)
        
        self.mock_llm_chat.reset_mock()
        self.clarifier.llm_chat = None
        
        mock_run_prompt.return_value = {"result": "测试结果"}
        
        result = await self.clarifier.run_llm("测试提示")
        
        mock_run_prompt.assert_called_once()
        self.assertEqual(result, {"result": "测试结果"})

    @patch('builtins.open', new_callable=mock_open)
    async def test_deep_clarification(self, mock_file):
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
        
        mock_result = "深度需求澄清结果"
        
        with patch.object(self.clarifier, 'run_llm') as mock_run_llm:
            mock_run_llm.return_value = mock_result  # 直接返回结果，而不是Future
            
            result = await self.clarifier.deep_clarification(requirement_analysis)
            
            mock_run_llm.assert_called_once()
            mock_file.assert_called_once()
            self.assertEqual(result, {"clarification_result": mock_result})

    @patch('builtins.open', new_callable=mock_open)
    async def test_deep_reasoning(self, mock_file):
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
        
        mock_result = "深度架构推理结果"
        
        with patch.object(self.clarifier, 'run_llm') as mock_run_llm:
            mock_run_llm.return_value = mock_result  # 直接返回结果，而不是Future
            
            result = await self.clarifier.deep_reasoning(requirement_analysis, architecture_analysis)
            
            mock_run_llm.assert_called_once()
            mock_file.assert_called_once()
            self.assertEqual(result, {"reasoning_result": mock_result})

    async def test_continue_from_user(self):
        """测试从用户继续"""
        self.clarifier.waiting_for_user = asyncio.Event()
        
        self.clarifier.continue_from_user()
        
        self.assertTrue(self.clarifier.waiting_for_user.is_set())

    @patch('importlib.import_module')
    async def test_integrate_legacy_modules(self, mock_import):
        """测试集成旧模块"""
        mock_module = MagicMock()
        mock_module.load_input_documents.return_value = {"doc1": "内容1"}
        mock_module.summarize_text.return_value = "摘要"
        mock_module.generate_summary_index.return_value = {"index": "内容"}
        
        mock_import.return_value = mock_module
        
        result = await self.clarifier.integrate_legacy_modules()
        
        mock_import.assert_called()
        self.assertEqual(result["documents"], {"doc1": "内容1"})
        self.assertEqual(result["summary"], "摘要")
        self.assertEqual(result["index"], {"index": "内容"})

    @patch('json.dump')
    @patch('pathlib.Path.mkdir')
    async def test_generate_granular_modules(self, mock_mkdir, mock_json_dump):
        """测试生成细粒度模块"""
        architecture_analysis = {
            "architecture_pattern": {
                "name": "分层架构",
                "description": "将系统分为多个层级"
            },
            "layers": [
                {
                    "name": "表现层",
                    "responsibility": "负责用户界面"
                },
                {
                    "name": "业务层",
                    "responsibility": "负责业务逻辑"
                },
                {
                    "name": "数据层",
                    "responsibility": "负责数据访问"
                }
            ],
            "core_components": [
                {
                    "name": "用户界面模块",
                    "layer": "表现层",
                    "description": "提供用户交互界面"
                },
                {
                    "name": "业务逻辑模块",
                    "layer": "业务层",
                    "description": "处理业务逻辑"
                },
                {
                    "name": "数据访问模块",
                    "layer": "数据层",
                    "description": "访问和管理数据"
                }
            ]
        }
        
        mock_llm_response = {
            "granular_modules": [
                {
                    "name": "登录页面",
                    "parent_module": "用户界面模块",
                    "layer": "表现层",
                    "type": "页面",
                    "description": "用户登录界面"
                },
                {
                    "name": "认证服务",
                    "parent_module": "业务逻辑模块",
                    "layer": "业务层",
                    "type": "服务",
                    "description": "处理用户认证逻辑"
                },
                {
                    "name": "用户仓储",
                    "parent_module": "数据访问模块",
                    "layer": "数据层",
                    "type": "仓储",
                    "description": "管理用户数据"
                }
            ]
        }
        
        m = mock_open()
        with patch('builtins.open', m):
            with patch.object(self.clarifier, 'run_llm') as mock_run_llm:
                mock_run_llm.return_value = mock_llm_response  # 直接返回结果，而不是Future
                
                with patch.object(Path, '__truediv__', return_value=Path('/mock/path')):
                    result = await self.clarifier.generate_granular_modules(architecture_analysis)
                    
                    mock_run_llm.assert_called_once()
                    self.assertEqual(result, mock_llm_response["granular_modules"])
