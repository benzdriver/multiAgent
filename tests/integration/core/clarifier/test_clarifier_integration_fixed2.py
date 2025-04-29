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
from core.clarifier.architecture_manager import ArchitectureManager
from core.clarifier.index_generator import MultiDimensionalIndexGenerator


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
        
        self.indices_dir = self.output_dir / "indices"
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        
        self.req_doc_path = self.input_dir / "requirements.md"
        with open(self.req_doc_path, "w", encoding="utf-8") as f:
            f.write("# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理")
            
        self.arch_doc_path = self.input_dir / "architecture.md"
        with open(self.arch_doc_path, "w", encoding="utf-8") as f:
            f.write("# 架构文档\n## 架构模式\n采用分层架构\n## 层级\n- 表现层\n- 业务层\n- 数据层")
        
        self.auth_module_dir = self.modules_dir / "AuthModule"
        self.auth_module_dir.mkdir(parents=True, exist_ok=True)
        
        self.auth_module_data = {
            "name": "AuthModule",
            "module_name": "AuthModule",
            "layer": "业务层",
            "domain": "安全",
            "responsibilities": ["用户认证", "权限管理"],
            "requirements": ["REQ-001"],
            "dependencies": []
        }
        
        with open(self.auth_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(self.auth_module_data, f, ensure_ascii=False, indent=2)
        
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
        
        self.architecture_manager = ArchitectureManager()
        self.architecture_manager.output_path = self.arch_output_dir
        
        self.architecture_reasoner = ArchitectureReasoner(
            architecture_manager=self.architecture_manager,
            llm_chat=self.mock_llm_chat,
            logger=self.clarifier.logger
        )
        
        self.index_generator = MultiDimensionalIndexGenerator(
            modules_dir=self.modules_dir,
            output_dir=self.indices_dir
        )

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_clarifier_with_document_processor(self):
        """测试Clarifier与DocumentProcessor的集成"""
        document_processor = DocumentProcessor(
            input_path=self.input_dir,
            logger=self.clarifier.logger
        )
        
        self.clarifier.document_processor = document_processor
        
        documents = await document_processor.read_all_markdown_files()
        
        self.assertEqual(len(documents), 2)
        self.assertIn("requirements.md", documents)
        self.assertIn("architecture.md", documents)
        
        with patch.object(document_processor, 'analyze_all_documents') as mock_analyze:
            mock_analyze.return_value = self.mock_llm_chat.return_value
            
            with patch.object(self.clarifier, '_file_based_clarification') as mock_file_clarification:
                mock_file_clarification.return_value = None
                
                with patch('builtins.input', return_value="1"):
                    await self.clarifier.start()
                    
                    mock_file_clarification.assert_called_once()

    async def test_clarifier_with_requirement_analyzer(self):
        """测试Clarifier与RequirementAnalyzer的集成"""
        requirement_analyzer = RequirementAnalyzer(
            output_dir=str(self.output_dir)
        )
        
        self.clarifier.requirement_analyzer = requirement_analyzer
        
        mock_document_processor = MagicMock()
        mock_document_processor.read_all_markdown_files.return_value = {
            "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理"
        }
        
        self.clarifier.document_processor = mock_document_processor
        
        mock_analyze = AsyncMock()
        mock_analyze.return_value = {
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
        
        mock_analyze_granular = AsyncMock()
        mock_analyze_granular.return_value = [
            {
                "module_name": "登录页面",
                "name": "登录页面",
                "layer": "表现层",
                "type": "页面",
                "description": "用户登录界面",
                "requirements": ["REQ-001"]
            },
            {
                "module_name": "认证服务",
                "name": "认证服务",
                "layer": "业务层",
                "type": "服务",
                "description": "处理用户认证逻辑",
                "requirements": ["REQ-001"]
            }
        ]
        
        with patch.object(RequirementAnalyzer, 'analyze_requirements', mock_analyze):
            with patch.object(RequirementAnalyzer, 'analyze_granular_modules', mock_analyze_granular):
                with patch.object(self.clarifier, '_read_all_markdown_files') as mock_read:
                    mock_read.return_value = {
                        "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理"
                    }
                    
                    with patch('core.clarifier.architecture_manager.ArchitectureManager.process_new_module') as mock_process:
                        mock_process.return_value = None
                        
                        with patch('core.clarifier.index_generator.MultiDimensionalIndexGenerator.generate_indices') as mock_generate:
                            mock_generate.return_value = {
                                "layer_index": {},
                                "domain_index": {},
                                "responsibility_index": {},
                                "requirement_module_index": {},
                                "cross_cutting_index": {}
                            }
                            
                            with patch.object(ArchitectureReasoner, 'check_all_issues') as mock_check:
                                mock_check.return_value = {}
                                
                                result = await self.clarifier.generate_granular_modules(
                                    input_path=str(self.input_dir),
                                    output_path=str(self.output_dir)
                                )
                                
                                self.assertIn("modules_count", result)
                                self.assertIn("issues_count", result)
                                self.assertEqual(result["modules_count"], 2)
                                self.assertEqual(result["issues_count"], 0)
                                
                                mock_analyze_granular.assert_called_once()

    async def test_clarifier_with_architecture_generator(self):
        """测试Clarifier与ArchitectureGenerator的集成"""
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
        
        mock_analyze = AsyncMock()
        mock_analyze.return_value = {
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
        }
        
        with patch.object(ArchitectureGenerator, 'analyze_architecture_needs', mock_analyze):
            with patch.object(self.clarifier, 'run_llm') as mock_run_llm:
                mock_run_llm.return_value = "深度推理结果"
                
                with patch('builtins.open', mock_open()) as mock_file:
                    result = await self.clarifier.deep_reasoning(requirement_analysis)
                    
                    self.assertIn("reasoning_result", result)
                    self.assertEqual(result["reasoning_result"], "深度推理结果")
                    
                    mock_run_llm.assert_called_once()

    async def test_clarifier_with_architecture_reasoner(self):
        """测试Clarifier与ArchitectureReasoner的集成"""
        self.clarifier.architecture_reasoner = self.architecture_reasoner
        
        self.clarifier.architecture_manager = self.architecture_manager
        
        with patch.object(ArchitectureReasoner, 'check_all_issues') as mock_check:
            mock_check.return_value = {
                "circular_dependencies": [],
                "naming_inconsistencies": [],
                "layer_violations": [],
                "responsibility_overlaps": [],
                "overall_consistency_issues": []
            }
            
            with patch.object(ArchitectureManager, 'process_new_module') as mock_process:
                mock_process.return_value = None
                
                result = await self.clarifier.integrate_legacy_modules(
                    input_path=str(self.input_dir),
                    output_path=str(self.output_dir)
                )
                
                self.assertIn("modules_count", result)
                self.assertIn("circular_dependencies", result)
                self.assertEqual(result["modules_count"], 1)
                self.assertEqual(result["circular_dependencies"], [])
                
                mock_check.assert_called_once()

    async def test_clarifier_with_index_generator(self):
        """测试Clarifier与MultiDimensionalIndexGenerator的集成"""
        with patch.object(self.clarifier, '_read_all_markdown_files') as mock_read:
            mock_read.return_value = {
                "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理"
            }
            
            mock_analyze = AsyncMock()
            mock_analyze.return_value = [
                {
                    "module_name": "登录页面",
                    "name": "登录页面",
                    "layer": "表现层",
                    "type": "页面",
                    "description": "用户登录界面",
                    "requirements": ["REQ-001"]
                }
            ]
            
            with patch.object(RequirementAnalyzer, 'analyze_granular_modules', mock_analyze):
                with patch('core.clarifier.architecture_manager.ArchitectureManager.process_new_module') as mock_process:
                    mock_process.return_value = None
                    
                    self.clarifier.index_generator = self.index_generator
                    
                    with patch.object(MultiDimensionalIndexGenerator, 'generate_indices') as mock_generate:
                        mock_generate.return_value = {
                            "layer_index": {
                                "表现层": ["登录页面"]
                            },
                            "domain_index": {},
                            "responsibility_index": {},
                            "requirement_module_index": {
                                "REQ-001": ["登录页面"]
                            },
                            "cross_cutting_index": {}
                        }
                        
                        with patch.object(ArchitectureReasoner, 'check_all_issues') as mock_check:
                            mock_check.return_value = {}
                            
                            result = await self.clarifier.generate_granular_modules(
                                input_path=str(self.input_dir),
                                output_path=str(self.output_dir)
                            )
                            
                            self.assertIn("modules_count", result)
                            self.assertIn("issues_count", result)
                            self.assertEqual(result["modules_count"], 1)
                            self.assertEqual(result["issues_count"], 0)
                            
                            mock_generate.assert_called_once()
                            
                            indices = mock_generate.return_value
                            self.assertIn("表现层", indices["layer_index"])
                            self.assertEqual(indices["layer_index"]["表现层"], ["登录页面"])
                            self.assertIn("REQ-001", indices["requirement_module_index"])
                            self.assertEqual(indices["requirement_module_index"]["REQ-001"], ["登录页面"])

    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        mock_document_processor = MagicMock()
        mock_document_processor.read_all_markdown_files.return_value = {
            "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理",
            "architecture.md": "# 架构文档\n## 架构模式\n采用分层架构\n## 层级\n- 表现层\n- 业务层\n- 数据层"
        }
        mock_document_processor.analyze_all_documents.return_value = self.mock_llm_chat.return_value
        
        self.clarifier.document_processor = mock_document_processor
        
        mock_requirement_analyzer = MagicMock()
        
        mock_analyze_requirements = AsyncMock()
        mock_analyze_requirements.return_value = {
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
        
        mock_analyze_granular = AsyncMock()
        mock_analyze_granular.return_value = [
            {
                "module_name": "登录页面",
                "name": "登录页面",
                "layer": "表现层",
                "type": "页面",
                "description": "用户登录界面",
                "requirements": ["REQ-001"]
            },
            {
                "module_name": "认证服务",
                "name": "认证服务",
                "layer": "业务层",
                "type": "服务",
                "description": "处理用户认证逻辑",
                "requirements": ["REQ-001"]
            }
        ]
        
        mock_requirement_analyzer.analyze_requirements = mock_analyze_requirements
        mock_requirement_analyzer.analyze_granular_modules = mock_analyze_granular
        
        self.clarifier.requirement_analyzer = mock_requirement_analyzer
        
        mock_architecture_generator = MagicMock()
        
        mock_analyze_architecture = AsyncMock()
        mock_analyze_architecture.return_value = {
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
        }
        
        mock_architecture_generator.analyze_architecture_needs = mock_analyze_architecture
        
        self.clarifier.architecture_generator = mock_architecture_generator
        
        mock_architecture_manager = MagicMock()
        mock_architecture_manager.process_new_module.return_value = None
        
        self.clarifier.architecture_manager = mock_architecture_manager
        
        mock_index_generator = MagicMock()
        mock_index_generator.generate_indices.return_value = {
            "layer_index": {
                "表现层": ["登录页面"],
                "业务层": ["认证服务"]
            },
            "domain_index": {},
            "responsibility_index": {},
            "requirement_module_index": {
                "REQ-001": ["登录页面", "认证服务"]
            },
            "cross_cutting_index": {}
        }
        
        self.clarifier.index_generator = mock_index_generator
        
        mock_architecture_reasoner = MagicMock()
        
        mock_check_issues = AsyncMock()
        mock_check_issues.return_value = {
            "circular_dependencies": [],
            "naming_inconsistencies": [],
            "layer_violations": [],
            "responsibility_overlaps": [],
            "overall_consistency_issues": []
        }
        
        mock_architecture_reasoner.check_all_issues = mock_check_issues
        
        self.clarifier.architecture_reasoner = mock_architecture_reasoner
        
        with patch.object(self.clarifier, 'run_llm') as mock_run_llm:
            mock_run_llm.return_value = "深度推理结果"
            
            with patch.object(self.clarifier, '_read_all_markdown_files') as mock_read:
                mock_read.return_value = {
                    "requirements.md": "# 需求文档\n## 用户认证\n系统应支持用户认证\n## 数据管理\n系统应支持数据管理",
                    "architecture.md": "# 架构文档\n## 架构模式\n采用分层架构\n## 层级\n- 表现层\n- 业务层\n- 数据层"
                }
                
                with patch('builtins.open', mock_open()) as mock_file:
                    
                    modules_result = await self.clarifier.generate_granular_modules(
                        input_path=str(self.input_dir),
                        output_path=str(self.output_dir)
                    )
                    
                    self.assertIn("modules_count", modules_result)
                    self.assertIn("issues_count", modules_result)
                    self.assertEqual(modules_result["modules_count"], 2)
                    self.assertEqual(modules_result["issues_count"], 0)
                    
                    reasoning_result = await self.clarifier.deep_reasoning(
                        mock_requirement_analyzer.analyze_requirements.return_value,
                        mock_architecture_generator.analyze_architecture_needs.return_value
                    )
                    
                    self.assertIn("reasoning_result", reasoning_result)
                    self.assertEqual(reasoning_result["reasoning_result"], "深度推理结果")
                    
                    integration_result = await self.clarifier.integrate_legacy_modules(
                        input_path=str(self.input_dir),
                        output_path=str(self.output_dir)
                    )
                    
                    self.assertIn("modules_count", integration_result)
                    self.assertIn("circular_dependencies", integration_result)
                    
                    mock_analyze_granular.assert_called_once()
                    mock_index_generator.generate_indices.assert_called_once()
                    mock_check_issues.assert_called()
