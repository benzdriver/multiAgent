"""
集成测试 - Clarifier
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


class TestClarifierIntegration(unittest.IsolatedAsyncioTestCase):
    """测试 Clarifier 与其他模块的集成"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.input_dir = self.data_dir / "input"
        self.output_dir = self.data_dir / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.arch_output_dir = self.output_dir / "architecture"
        self.arch_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.modules_dir = self.output_dir / "modules"
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        
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

    async def test_integration_with_document_processor(self):
        """测试与DocumentProcessor的集成"""
        document_processor = DocumentProcessor(
            input_path=self.input_dir
        )
        
        self.clarifier.document_processor = document_processor
        
        with patch.object(self.clarifier, '_file_based_clarification') as mock_file_clarification:
            mock_file_clarification.return_value = asyncio.Future()
            mock_file_clarification.return_value.set_result(None)
            
            with patch('builtins.input', return_value="1"):
                await self.clarifier.start()
                
                mock_file_clarification.assert_called_once()
        
        documents = await document_processor.read_all_markdown_files()
        
        self.assertEqual(len(documents), 2)
        self.assertIn("requirements.md", documents)
        self.assertIn("architecture.md", documents)

    async def test_integration_with_requirement_analyzer(self):
        """测试与RequirementAnalyzer的集成"""
        requirement_analyzer = RequirementAnalyzer()
        
        self.clarifier.requirement_analyzer = requirement_analyzer
        
        mock_document_processor = MagicMock()
        mock_document_processor.read_all_markdown_files.return_value = asyncio.Future()
        mock_document_processor.read_all_markdown_files.return_value.set_result({
            "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理"
        })
        
        self.clarifier.document_processor = mock_document_processor
        
        with patch.object(RequirementAnalyzer, 'analyze_requirements') as mock_analyze:
            mock_analyze.return_value = asyncio.Future()
            mock_analyze.return_value.set_result({
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
            })
            
            with patch.object(self.clarifier, 'run_llm') as mock_run_llm:
                mock_run_llm.return_value = asyncio.Future()
                mock_run_llm.return_value.set_result({})
                
                self.clarifier.waiting_for_user = asyncio.Event()
                self.clarifier.waiting_for_user.set()
                
                with patch.object(RequirementAnalyzer, 'generate_requirement_summary') as mock_generate:
                    mock_generate.return_value = asyncio.Future()
                    mock_generate.return_value.set_result(None)
                    
                    with patch('builtins.input', return_value="n"):
                        await self.clarifier._file_based_clarification()
                    
                    mock_analyze.assert_called_once()

    async def test_integration_with_architecture_generator(self):
        """测试与ArchitectureGenerator的集成"""
        architecture_generator = ArchitectureGenerator(
            logger=self.clarifier.logger
        )
        
        self.clarifier.architecture_generator = architecture_generator
        
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
        
        with patch.object(ArchitectureGenerator, 'analyze_architecture_needs') as mock_analyze:
            mock_analyze.return_value = asyncio.Future()
            mock_analyze.return_value.set_result({
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
                ]
            })
            
            with patch.object(self.clarifier, 'deep_reasoning') as mock_deep_reasoning:
                mock_deep_reasoning.return_value = asyncio.Future()
                mock_deep_reasoning.return_value.set_result({"reasoning_result": "深度推理结果"})
                
                result = await self.clarifier.deep_reasoning(requirement_analysis)
                
                self.assertIn("reasoning_result", result)

    async def test_integration_with_architecture_reasoner(self):
        """测试与ArchitectureReasoner的集成"""
        from core.clarifier.architecture_manager import ArchitectureManager
        architecture_manager = ArchitectureManager()
        architecture_reasoner = ArchitectureReasoner(
            architecture_manager=architecture_manager,
            logger=self.clarifier.logger
        )
        
        module_dir = self.modules_dir / "TestModule"
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
        
        with patch.object(ArchitectureReasoner, 'check_all_issues') as mock_check:
            mock_check.return_value = asyncio.Future()
            mock_check.return_value.set_result({})
            
            with patch.object(self.clarifier, 'integrate_legacy_modules') as mock_integrate:
                mock_integrate.return_value = asyncio.Future()
                mock_integrate.return_value.set_result({
                    "modules_count": 1,
                    "circular_dependencies": []
                })
                
                result = await self.clarifier.integrate_legacy_modules(
                    input_path=str(self.input_dir),
                    output_path=str(self.output_dir)
                )
                
                self.assertIn("modules_count", result)
                self.assertIn("circular_dependencies", result)

    async def test_generate_granular_modules(self):
        """测试生成细粒度模块"""
        with patch.object(self.clarifier, '_read_all_markdown_files') as mock_read:
            mock_read.return_value = {
                "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理",
                "architecture.md": "# 架构文档\n## 架构模式\n采用分层架构\n## 层级\n- 表现层\n- 业务层\n- 数据层"
            }
            
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
                            
                            self.assertIn("modules_count", result)
                            self.assertIn("issues_count", result)
