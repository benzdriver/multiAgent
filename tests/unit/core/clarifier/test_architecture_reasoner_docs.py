"""
单元测试 - ArchitectureReasoner 文档生成和验证方法
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import asyncio
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime

from core.clarifier.architecture_reasoner import ArchitectureReasoner
from core.clarifier.architecture_manager import ArchitectureManager


class TestArchitectureReasonerDocs(unittest.IsolatedAsyncioTestCase):
    """测试 ArchitectureReasoner 文档生成和验证方法"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.arch_output_dir = self.output_dir / "architecture"
        self.arch_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.mock_architecture_manager = MagicMock()
        self.mock_architecture_manager.index.requirement_module_index = {
            "REQ-001": ["UIComponent"],
            "REQ-002": ["ServiceComponent"]
        }
        self.mock_architecture_manager.index.responsibility_index = {
            "显示界面": {
                "modules": ["UIComponent"],
                "objects": ["UI"],
                "patterns": ["MVC"]
            },
            "处理业务逻辑": {
                "modules": ["ServiceComponent"],
                "objects": ["Service"],
                "patterns": ["MVC"]
            }
        }
        self.mock_architecture_manager.index.dependency_graph = {
            "UIComponent": {
                "depends_on": ["ServiceComponent"],
                "depended_by": [],
                "pattern": "MVC",
                "layer": "presentation"
            },
            "ServiceComponent": {
                "depends_on": ["DataComponent"],
                "depended_by": ["UIComponent"],
                "pattern": "MVC",
                "layer": "business"
            },
            "DataComponent": {
                "depends_on": [],
                "depended_by": ["ServiceComponent"],
                "pattern": "MVC",
                "layer": "data"
            }
        }
        self.mock_architecture_manager.index.layer_index = {
            "presentation": {
                "UIComponent": {
                    "name": "UIComponent",
                    "responsibilities": ["显示界面"]
                }
            },
            "business": {
                "ServiceComponent": {
                    "name": "ServiceComponent",
                    "responsibilities": ["处理业务逻辑"]
                }
            },
            "data": {
                "DataComponent": {
                    "name": "DataComponent",
                    "responsibilities": ["数据访问"]
                }
            }
        }
        
        self.mock_llm_chat = AsyncMock()
        self.mock_llm_chat.return_value = {"content": "模拟的LLM响应"}
        
        self.mock_logger = MagicMock()
        
        self.reasoner = ArchitectureReasoner(
            architecture_manager=self.mock_architecture_manager,
            llm_chat=self.mock_llm_chat,
            logger=self.mock_logger,
            output_path=self.arch_output_dir
        )

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._generate_overview_doc')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._generate_detailed_design_doc')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._generate_interface_doc')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._generate_deployment_doc')
    async def test_generate_architecture_docs(self, mock_deployment, mock_interface, mock_detailed, mock_overview):
        """测试生成架构文档"""
        mock_overview.return_value = "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计..."
        mock_detailed.return_value = "# 详细设计\n\n## 模块详情\n\n本系统包含以下模块..."
        mock_interface.return_value = "# 接口文档\n\n## 接口定义\n\n本系统定义了以下接口..."
        mock_deployment.return_value = "# 部署文档\n\n## 部署要求\n\n本系统的部署要求如下..."
        
        await self.reasoner._generate_architecture_docs()
        
        mock_overview.assert_called_once()
        mock_detailed.assert_called_once()
        mock_interface.assert_called_once()
        mock_deployment.assert_called_once()
        
        self.assertTrue((self.arch_output_dir / "01_architecture_overview.md").exists())
        self.assertTrue((self.arch_output_dir / "02_detailed_design.md").exists())
        self.assertTrue((self.arch_output_dir / "03_interfaces.md").exists())
        self.assertTrue((self.arch_output_dir / "04_deployment.md").exists())
        
        self.assertEqual((self.arch_output_dir / "01_architecture_overview.md").read_text(), 
                         "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计...")
        self.assertEqual((self.arch_output_dir / "02_detailed_design.md").read_text(), 
                         "# 详细设计\n\n## 模块详情\n\n本系统包含以下模块...")
        self.assertEqual((self.arch_output_dir / "03_interfaces.md").read_text(), 
                         "# 接口文档\n\n## 接口定义\n\n本系统定义了以下接口...")
        self.assertEqual((self.arch_output_dir / "04_deployment.md").read_text(), 
                         "# 部署文档\n\n## 部署要求\n\n本系统的部署要求如下...")
        
        self.mock_logger.log.assert_any_call("\n📝 生成架构文档...", role="system")
        self.mock_logger.log.assert_any_call("✅ 架构文档生成完成", role="system")

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._get_llm_response')
    async def test_generate_overview_doc(self, mock_get_llm_response):
        """测试生成架构概览文档"""
        mock_get_llm_response.return_value = {"content": "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计..."}
        
        arch_state = {
            "timestamp": datetime.now().isoformat(),
            "requirement_module_index": {"REQ-001": ["UIComponent"]},
            "responsibility_index": {"显示界面": {"modules": ["UIComponent"]}},
            "dependency_graph": {"UIComponent": {"depends_on": []}},
            "layer_index": {"presentation": {"UIComponent": {}}}
        }
        
        result = await self.reasoner._generate_overview_doc(arch_state)
        
        self.assertEqual(result, "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计...")
        
        mock_get_llm_response.assert_called_once()
        
        mock_get_llm_response.reset_mock()
        mock_get_llm_response.return_value = {"text": "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计..."}
        
        result = await self.reasoner._generate_overview_doc(arch_state)
        self.assertEqual(result, "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计...")
        
        mock_get_llm_response.reset_mock()
        mock_get_llm_response.return_value = "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计..."
        
        result = await self.reasoner._generate_overview_doc(arch_state)
        self.assertEqual(result, "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计...")
        
        mock_get_llm_response.reset_mock()
        mock_get_llm_response.return_value = {"result": {"title": "架构概览"}}
        
        result = await self.reasoner._generate_overview_doc(arch_state)
        self.assertEqual(result, '{\n  "result": {\n    "title": "架构概览"\n  }\n}')

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._get_llm_response')
    async def test_generate_detailed_design_doc(self, mock_get_llm_response):
        """测试生成详细设计文档"""
        mock_get_llm_response.return_value = {"content": "# 详细设计\n\n## 模块详情\n\n本系统包含以下模块..."}
        
        arch_state = {
            "timestamp": datetime.now().isoformat(),
            "requirement_module_index": {"REQ-001": ["UIComponent"]},
            "responsibility_index": {"显示界面": {"modules": ["UIComponent"]}},
            "dependency_graph": {"UIComponent": {"depends_on": []}},
            "layer_index": {"presentation": {"UIComponent": {}}}
        }
        
        result = await self.reasoner._generate_detailed_design_doc(arch_state)
        
        self.assertEqual(result, "# 详细设计\n\n## 模块详情\n\n本系统包含以下模块...")
        
        mock_get_llm_response.assert_called_once()

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._get_llm_response')
    async def test_generate_interface_doc(self, mock_get_llm_response):
        """测试生成接口文档"""
        mock_get_llm_response.return_value = {"content": "# 接口文档\n\n## 接口定义\n\n本系统定义了以下接口..."}
        
        arch_state = {
            "timestamp": datetime.now().isoformat(),
            "requirement_module_index": {"REQ-001": ["UIComponent"]},
            "responsibility_index": {"显示界面": {"modules": ["UIComponent"]}},
            "dependency_graph": {"UIComponent": {"depends_on": []}},
            "layer_index": {"presentation": {"UIComponent": {}}}
        }
        
        result = await self.reasoner._generate_interface_doc(arch_state)
        
        self.assertEqual(result, "# 接口文档\n\n## 接口定义\n\n本系统定义了以下接口...")
        
        mock_get_llm_response.assert_called_once()

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._get_llm_response')
    async def test_generate_deployment_doc(self, mock_get_llm_response):
        """测试生成部署文档"""
        mock_get_llm_response.return_value = {"content": "# 部署文档\n\n## 部署要求\n\n本系统的部署要求如下..."}
        
        arch_state = {
            "timestamp": datetime.now().isoformat(),
            "requirement_module_index": {"REQ-001": ["UIComponent"]},
            "responsibility_index": {"显示界面": {"modules": ["UIComponent"]}},
            "dependency_graph": {"UIComponent": {"depends_on": []}},
            "layer_index": {"presentation": {"UIComponent": {}}}
        }
        
        result = await self.reasoner._generate_deployment_doc(arch_state)
        
        self.assertEqual(result, "# 部署文档\n\n## 部署要求\n\n本系统的部署要求如下...")
        
        mock_get_llm_response.assert_called_once()

    async def test_validate_responsibilities(self):
        """测试验证职责"""
        result = self.reasoner._validate_responsibilities(["显示界面", "处理用户输入"])
        self.assertTrue(result)
        
        result = self.reasoner._validate_responsibilities([])
        self.assertFalse(result)
        
        result = self.reasoner._validate_responsibilities([""])
        self.assertFalse(result)

    async def test_validate_components(self):
        """测试验证组件"""
        result = self.reasoner._validate_components(["UIComponent", "ServiceComponent"])
        self.assertTrue(result)
        
        result = self.reasoner._validate_components([])
        self.assertFalse(result)
        
        result = self.reasoner._validate_components([""])
        self.assertFalse(result)

    async def test_validate_dependencies(self):
        """测试验证依赖"""
        result = self.reasoner._validate_dependencies(["UIComponent", "ServiceComponent"])
        self.assertTrue(result)
        
        result = self.reasoner._validate_dependencies([])
        self.assertTrue(result)  # 空依赖是有效的
        
        result = self.reasoner._validate_dependencies([""])
        self.assertFalse(result)

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._validate_responsibilities')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._validate_components')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._validate_with_relationships')
    async def test_validate_layer_design(self, mock_relationships, mock_components, mock_responsibilities):
        """测试验证层级设计"""
        mock_responsibilities.return_value = True
        mock_components.return_value = True
        mock_relationships.return_value = {"has_issues": False, "issues": []}
        
        layer_name = "presentation"
        layer_info = {
            "responsibilities": ["显示界面", "处理用户输入"],
            "components": ["UIComponent"]
        }
        related_components = {
            "by_dependency": ["ServiceComponent"],
            "by_feature": ["DataComponent"],
            "by_keyword": [],
            "by_responsibility": []
        }
        
        result = await self.reasoner._validate_layer_design(layer_name, layer_info, related_components)
        
        self.assertFalse(result["has_issues"])
        self.assertEqual(result["issues"], [])
        
        mock_responsibilities.assert_called_once_with(["显示界面", "处理用户输入"])
        mock_components.assert_called_once_with(["UIComponent"])
        mock_relationships.assert_called_once()
        
        mock_responsibilities.reset_mock()
        mock_components.reset_mock()
        mock_relationships.reset_mock()
        
        mock_responsibilities.return_value = False
        
        result = await self.reasoner._validate_layer_design(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0]["type"], "missing_responsibilities")
        
        mock_responsibilities.reset_mock()
        mock_components.reset_mock()
        mock_relationships.reset_mock()
        
        mock_responsibilities.return_value = True
        mock_components.return_value = False
        
        result = await self.reasoner._validate_layer_design(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0]["type"], "missing_components")
        
        mock_responsibilities.reset_mock()
        mock_components.reset_mock()
        mock_relationships.reset_mock()
        
        mock_responsibilities.return_value = True
        mock_components.return_value = True
        mock_relationships.return_value = {
            "has_issues": True,
            "issues": [
                {"type": "relationship_issue", "description": "关系问题"}
            ]
        }
        
        result = await self.reasoner._validate_layer_design(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0]["type"], "relationship_issue")

    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._check_feature_overlaps')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._check_domain_consistency')
    @patch('core.clarifier.architecture_reasoner.ArchitectureReasoner._check_dependency_rationality')
    async def test_validate_with_relationships(self, mock_dependency, mock_domain, mock_feature):
        """测试验证关系"""
        mock_feature.return_value = []
        mock_domain.return_value = []
        mock_dependency.return_value = []
        
        layer_name = "presentation"
        layer_info = {
            "responsibilities": ["显示界面", "处理用户输入"],
            "components": ["UIComponent"]
        }
        related_components = {
            "by_dependency": ["ServiceComponent"],
            "by_feature": ["DataComponent"],
            "by_keyword": [],
            "by_responsibility": []
        }
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertFalse(result["has_issues"])
        self.assertEqual(result["issues"], [])
        
        mock_feature.assert_called_once()
        mock_domain.assert_called_once()
        mock_dependency.assert_called_once()
        
        mock_feature.reset_mock()
        mock_domain.reset_mock()
        mock_dependency.reset_mock()
        
        mock_feature.return_value = [{"type": "feature_overlap", "description": "特性重叠"}]
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0]["type"], "feature_overlap")
        
        mock_feature.reset_mock()
        mock_domain.reset_mock()
        mock_dependency.reset_mock()
        
        mock_feature.return_value = []
        mock_domain.return_value = [{"type": "domain_inconsistency", "description": "领域不一致"}]
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0]["type"], "domain_inconsistency")
        
        mock_feature.reset_mock()
        mock_domain.reset_mock()
        mock_dependency.reset_mock()
        
        mock_feature.return_value = []
        mock_domain.return_value = []
        mock_dependency.return_value = [{"type": "dependency_issue", "description": "依赖问题"}]
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0]["type"], "dependency_issue")
        
        mock_feature.reset_mock()
        mock_domain.reset_mock()
        mock_dependency.reset_mock()
        
        mock_feature.return_value = [{"type": "feature_overlap", "description": "特性重叠"}]
        mock_domain.return_value = [{"type": "domain_inconsistency", "description": "领域不一致"}]
        mock_dependency.return_value = [{"type": "dependency_issue", "description": "依赖问题"}]
        
        result = await self.reasoner._validate_with_relationships(layer_name, layer_info, related_components)
        
        self.assertTrue(result["has_issues"])
        self.assertEqual(len(result["issues"]), 3)

    async def test_check_feature_overlaps(self):
        """测试检查特性重叠"""
        layer_name = "presentation"
        layer_info = {
            "responsibilities": ["显示界面", "处理用户输入"],
            "components": ["UIComponent"],
            "features": ["UI渲染", "用户交互"]
        }
        related_components = {
            "by_feature": [
                {
                    "name": "DataComponent",
                    "features": ["数据访问", "数据验证"]
                }
            ]
        }
        
        result = self.reasoner._check_feature_overlaps(layer_name, layer_info, related_components)
        
        self.assertEqual(result, [])
        
        layer_info["features"] = ["UI渲染", "数据访问"]
        
        result = self.reasoner._check_feature_overlaps(layer_name, layer_info, related_components)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "feature_overlap")
        self.assertEqual(result[0]["overlapping_features"], ["数据访问"])
        self.assertEqual(result[0]["components"], ["UIComponent", "DataComponent"])

    async def test_check_domain_consistency(self):
        """测试检查领域一致性"""
        layer_name = "presentation"
        layer_info = {
            "responsibilities": ["显示界面", "处理用户输入"],
            "components": ["UIComponent"],
            "domains": ["前端", "UI"]
        }
        related_components = {
            "by_dependency": [
                {
                    "name": "ServiceComponent",
                    "domains": ["业务", "服务"]
                }
            ]
        }
        
        result = self.reasoner._check_domain_consistency(layer_name, layer_info, related_components)
        
        self.assertEqual(result, [])
        
        layer_info["domains"] = ["前端", "业务"]
        
        result = self.reasoner._check_domain_consistency(layer_name, layer_info, related_components)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "domain_inconsistency")
        self.assertEqual(result[0]["overlapping_domains"], ["业务"])
        self.assertEqual(result[0]["components"], ["UIComponent", "ServiceComponent"])

    async def test_check_dependency_rationality(self):
        """测试检查依赖合理性"""
        layer_name = "presentation"
        layer_info = {
            "responsibilities": ["显示界面", "处理用户输入"],
            "components": ["UIComponent"],
            "dependencies": ["ServiceComponent"]
        }
        related_components = {
            "by_dependency": [
                {
                    "name": "ServiceComponent",
                    "layer": "business"
                }
            ]
        }
        
        result = self.reasoner._check_dependency_rationality(layer_name, layer_info, related_components)
        
        self.assertEqual(result, [])
        
        related_components["by_dependency"][0]["layer"] = "presentation"
        
        result = self.reasoner._check_dependency_rationality(layer_name, layer_info, related_components)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "same_layer_dependency")
        self.assertEqual(result[0]["layer"], "presentation")
        self.assertEqual(result[0]["components"], ["UIComponent", "ServiceComponent"])
        
        related_components["by_dependency"][0]["layer"] = "data"
        layer_name = "business"
        
        result = self.reasoner._check_dependency_rationality(layer_name, layer_info, related_components)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "layer_violation")
        self.assertEqual(result[0]["from_layer"], "business")
        self.assertEqual(result[0]["to_layer"], "data")
        self.assertEqual(result[0]["components"], ["UIComponent", "ServiceComponent"])


if __name__ == '__main__':
    unittest.main()
