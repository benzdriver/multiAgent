"""
集成测试 - ArchitectureReasoner 类
"""
import unittest
import asyncio
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from core.clarifier.architecture_reasoner import ArchitectureReasoner
from core.clarifier.architecture_manager import ArchitectureManager


class TestArchitectureReasonerIntegration(unittest.IsolatedAsyncioTestCase):
    """测试 ArchitectureReasoner 与其他组件的集成"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.arch_output_dir = self.output_dir / "architecture"
        self.arch_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.modules_dir = self.output_dir / "modules"
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        
        self.create_test_modules()
        
        self.architecture_manager = ArchitectureManager()
        self.architecture_manager.output_path = self.arch_output_dir
        
        self.mock_llm_chat = AsyncMock()
        self.mock_llm_chat.return_value = {
            "result": "模拟的LLM响应",
            "analysis": {
                "issues": []
            }
        }
        
        self.mock_logger = MagicMock()
        
        self.reasoner = ArchitectureReasoner(
            architecture_manager=self.architecture_manager,
            llm_chat=self.mock_llm_chat,
            logger=self.mock_logger,
            output_path=self.arch_output_dir
        )

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    def create_test_modules(self):
        """创建测试模块"""
        ui_module_dir = self.modules_dir / "UIComponent"
        ui_module_dir.mkdir(parents=True, exist_ok=True)
        
        ui_module_data = {
            "name": "UIComponent",
            "module_name": "UIComponent",
            "description": "UI组件",
            "responsibilities": ["显示界面", "处理用户交互"],
            "dependencies": ["ServiceComponent"],
            "interfaces": ["IUIComponent"],
            "pattern": "MVC",
            "layer": "presentation",
            "features": ["UI渲染", "用户交互"],
            "domains": ["前端"],
            "technologies": ["React"],
            "path": "src/presentation/ui"
        }
        
        with open(ui_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(ui_module_data, f, ensure_ascii=False, indent=2)
        
        service_module_dir = self.modules_dir / "ServiceComponent"
        service_module_dir.mkdir(parents=True, exist_ok=True)
        
        service_module_data = {
            "name": "ServiceComponent",
            "module_name": "ServiceComponent",
            "description": "服务组件",
            "responsibilities": ["处理业务逻辑", "调用数据访问层"],
            "dependencies": ["DataComponent"],
            "interfaces": ["IServiceComponent"],
            "pattern": "MVC",
            "layer": "business",
            "features": ["业务处理", "数据验证"],
            "domains": ["业务"],
            "technologies": ["Spring"],
            "path": "src/business/service"
        }
        
        with open(service_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(service_module_data, f, ensure_ascii=False, indent=2)
        
        data_module_dir = self.modules_dir / "DataComponent"
        data_module_dir.mkdir(parents=True, exist_ok=True)
        
        data_module_data = {
            "name": "DataComponent",
            "module_name": "DataComponent",
            "description": "数据组件",
            "responsibilities": ["数据访问", "数据持久化"],
            "dependencies": [],
            "interfaces": ["IDataComponent"],
            "pattern": "MVC",
            "layer": "data",
            "features": ["数据访问", "数据持久化"],
            "domains": ["数据"],
            "technologies": ["JPA"],
            "path": "src/data/repository"
        }
        
        with open(data_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(data_module_data, f, ensure_ascii=False, indent=2)
        
        circular_module_dir = self.modules_dir / "CircularComponent"
        circular_module_dir.mkdir(parents=True, exist_ok=True)
        
        circular_module_data = {
            "name": "CircularComponent",
            "module_name": "CircularComponent",
            "description": "循环依赖测试组件",
            "responsibilities": ["测试循环依赖"],
            "dependencies": ["UIComponent"],
            "interfaces": ["ICircularComponent"],
            "pattern": "MVC",
            "layer": "business",
            "features": ["循环依赖测试"],
            "domains": ["测试"],
            "technologies": ["Java"],
            "path": "src/business/circular"
        }
        
        with open(circular_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(circular_module_data, f, ensure_ascii=False, indent=2)
        
        ui_module_data["dependencies"].append("CircularComponent")
        
        with open(ui_module_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(ui_module_data, f, ensure_ascii=False, indent=2)

    @patch('core.clarifier.architecture_reasoner.run_prompt')
    async def test_integration_with_architecture_manager(self, mock_run_prompt):
        """测试与 ArchitectureManager 的集成"""
        mock_run_prompt.return_value = {
            "result": "模拟的LLM响应",
            "analysis": {
                "issues": []
            }
        }
        
        architecture_understanding = {
            "architecture_design": {
                "patterns": [
                    {
                        "name": "MVC",
                        "layers": [
                            {
                                "name": "presentation",
                                "components": [
                                    {
                                        "name": "UIComponent",
                                        "description": "UI组件",
                                        "responsibilities": ["显示界面"],
                                        "dependencies": ["ServiceComponent", "CircularComponent"],
                                        "interfaces": ["IUIComponent"],
                                        "features": ["UI渲染"],
                                        "domains": ["前端"],
                                        "technologies": ["React"],
                                        "requirements": ["REQ-001"]
                                    }
                                ]
                            },
                            {
                                "name": "business",
                                "components": [
                                    {
                                        "name": "ServiceComponent",
                                        "description": "服务组件",
                                        "responsibilities": ["处理业务逻辑"],
                                        "dependencies": ["DataComponent"],
                                        "interfaces": ["IServiceComponent"],
                                        "features": ["业务处理"],
                                        "domains": ["业务"],
                                        "technologies": ["Spring"],
                                        "requirements": ["REQ-002"]
                                    },
                                    {
                                        "name": "CircularComponent",
                                        "description": "循环依赖测试组件",
                                        "responsibilities": ["测试循环依赖"],
                                        "dependencies": ["UIComponent"],
                                        "interfaces": ["ICircularComponent"],
                                        "features": ["循环依赖测试"],
                                        "domains": ["测试"],
                                        "technologies": ["Java"],
                                        "requirements": ["REQ-003"]
                                    }
                                ]
                            },
                            {
                                "name": "data",
                                "components": [
                                    {
                                        "name": "DataComponent",
                                        "description": "数据组件",
                                        "responsibilities": ["数据访问"],
                                        "dependencies": [],
                                        "interfaces": ["IDataComponent"],
                                        "features": ["数据访问"],
                                        "domains": ["数据"],
                                        "technologies": ["JPA"],
                                        "requirements": ["REQ-004"]
                                    }
                                ]
                            }
                        ],
                        "interfaces": ["IUIComponent", "IServiceComponent", "IDataComponent", "ICircularComponent"],
                        "dependencies": {
                            "presentation": ["business"],
                            "business": ["data"]
                        }
                    }
                ]
            }
        }
        
        await self.reasoner.populate_architecture_index(architecture_understanding)
        
        self.assertIn("UIComponent", self.architecture_manager.index.dependency_graph)
        self.assertIn("ServiceComponent", self.architecture_manager.index.dependency_graph)
        self.assertIn("DataComponent", self.architecture_manager.index.dependency_graph)
        self.assertIn("CircularComponent", self.architecture_manager.index.dependency_graph)
        
        self.assertIn("ServiceComponent", self.architecture_manager.index.dependency_graph["UIComponent"]["depends_on"])
        self.assertIn("CircularComponent", self.architecture_manager.index.dependency_graph["UIComponent"]["depends_on"])
        self.assertIn("DataComponent", self.architecture_manager.index.dependency_graph["ServiceComponent"]["depends_on"])
        self.assertIn("UIComponent", self.architecture_manager.index.dependency_graph["CircularComponent"]["depends_on"])
        
        self.assertIn("UIComponent", self.architecture_manager.index.dependency_graph["ServiceComponent"]["depended_by"])
        self.assertIn("ServiceComponent", self.architecture_manager.index.dependency_graph["DataComponent"]["depended_by"])
        self.assertIn("CircularComponent", self.architecture_manager.index.dependency_graph["UIComponent"]["depended_by"])
        self.assertIn("UIComponent", self.architecture_manager.index.dependency_graph["CircularComponent"]["depended_by"])

    @patch('core.clarifier.architecture_reasoner.run_prompt')
    async def test_check_circular_dependencies(self, mock_run_prompt):
        """测试检查循环依赖"""
        mock_run_prompt.return_value = {
            "result": "模拟的LLM响应",
            "analysis": {
                "issues": []
            }
        }
        
        architecture_understanding = {
            "architecture_design": {
                "patterns": [
                    {
                        "name": "MVC",
                        "layers": [
                            {
                                "name": "presentation",
                                "components": [
                                    {
                                        "name": "UIComponent",
                                        "description": "UI组件",
                                        "responsibilities": ["显示界面"],
                                        "dependencies": ["ServiceComponent", "CircularComponent"],
                                        "interfaces": ["IUIComponent"],
                                        "features": ["UI渲染"],
                                        "domains": ["前端"],
                                        "technologies": ["React"],
                                        "requirements": ["REQ-001"]
                                    }
                                ]
                            },
                            {
                                "name": "business",
                                "components": [
                                    {
                                        "name": "ServiceComponent",
                                        "description": "服务组件",
                                        "responsibilities": ["处理业务逻辑"],
                                        "dependencies": ["DataComponent"],
                                        "interfaces": ["IServiceComponent"],
                                        "features": ["业务处理"],
                                        "domains": ["业务"],
                                        "technologies": ["Spring"],
                                        "requirements": ["REQ-002"]
                                    },
                                    {
                                        "name": "CircularComponent",
                                        "description": "循环依赖测试组件",
                                        "responsibilities": ["测试循环依赖"],
                                        "dependencies": ["UIComponent"],
                                        "interfaces": ["ICircularComponent"],
                                        "features": ["循环依赖测试"],
                                        "domains": ["测试"],
                                        "technologies": ["Java"],
                                        "requirements": ["REQ-003"]
                                    }
                                ]
                            },
                            {
                                "name": "data",
                                "components": [
                                    {
                                        "name": "DataComponent",
                                        "description": "数据组件",
                                        "responsibilities": ["数据访问"],
                                        "dependencies": [],
                                        "interfaces": ["IDataComponent"],
                                        "features": ["数据访问"],
                                        "domains": ["数据"],
                                        "technologies": ["JPA"],
                                        "requirements": ["REQ-004"]
                                    }
                                ]
                            }
                        ],
                        "interfaces": ["IUIComponent", "IServiceComponent", "IDataComponent", "ICircularComponent"],
                        "dependencies": {
                            "presentation": ["business"],
                            "business": ["data"]
                        }
                    }
                ]
            }
        }
        
        await self.reasoner.populate_architecture_index(architecture_understanding)
        
        issues = await self.reasoner.check_all_issues()
        
        self.assertIn("circular_dependencies", issues)
        self.assertTrue(len(issues["circular_dependencies"]) > 0)
        
        circular_deps = issues["circular_dependencies"]
        found_circular = False
        for dep in circular_deps:
            if "UIComponent" in dep and "CircularComponent" in dep:
                found_circular = True
                break
        
        self.assertTrue(found_circular, "未检测到 UIComponent 和 CircularComponent 之间的循环依赖")

    @patch('core.clarifier.architecture_reasoner.run_prompt')
    async def test_check_module_issues(self, mock_run_prompt):
        """测试检查模块问题"""
        mock_run_prompt.return_value = {
            "result": "模拟的LLM响应",
            "analysis": {
                "issues": []
            }
        }
        
        architecture_understanding = {
            "architecture_design": {
                "patterns": [
                    {
                        "name": "MVC",
                        "layers": [
                            {
                                "name": "presentation",
                                "components": [
                                    {
                                        "name": "UIComponent",
                                        "description": "UI组件",
                                        "responsibilities": ["显示界面"],
                                        "dependencies": ["ServiceComponent", "CircularComponent"],
                                        "interfaces": ["IUIComponent"],
                                        "features": ["UI渲染"],
                                        "domains": ["前端"],
                                        "technologies": ["React"],
                                        "requirements": ["REQ-001"]
                                    }
                                ]
                            },
                            {
                                "name": "business",
                                "components": [
                                    {
                                        "name": "ServiceComponent",
                                        "description": "服务组件",
                                        "responsibilities": ["处理业务逻辑"],
                                        "dependencies": ["DataComponent"],
                                        "interfaces": ["IServiceComponent"],
                                        "features": ["业务处理"],
                                        "domains": ["业务"],
                                        "technologies": ["Spring"],
                                        "requirements": ["REQ-002"]
                                    },
                                    {
                                        "name": "CircularComponent",
                                        "description": "循环依赖测试组件",
                                        "responsibilities": ["测试循环依赖"],
                                        "dependencies": ["UIComponent"],
                                        "interfaces": ["ICircularComponent"],
                                        "features": ["循环依赖测试"],
                                        "domains": ["测试"],
                                        "technologies": ["Java"],
                                        "requirements": ["REQ-003"]
                                    }
                                ]
                            },
                            {
                                "name": "data",
                                "components": [
                                    {
                                        "name": "DataComponent",
                                        "description": "数据组件",
                                        "responsibilities": ["数据访问"],
                                        "dependencies": [],
                                        "interfaces": ["IDataComponent"],
                                        "features": ["数据访问"],
                                        "domains": ["数据"],
                                        "technologies": ["JPA"],
                                        "requirements": ["REQ-004"]
                                    }
                                ]
                            }
                        ],
                        "interfaces": ["IUIComponent", "IServiceComponent", "IDataComponent", "ICircularComponent"],
                        "dependencies": {
                            "presentation": ["business"],
                            "business": ["data"]
                        }
                    }
                ]
            }
        }
        
        await self.reasoner.populate_architecture_index(architecture_understanding)
        
        issues = await self.reasoner.check_module_issues("UIComponent")
        
        self.assertIn("circular_dependencies", issues)
        self.assertTrue(len(issues["circular_dependencies"]) > 0)
        
        circular_deps = issues["circular_dependencies"]
        found_circular = False
        for dep in circular_deps:
            if "UIComponent" in dep and "CircularComponent" in dep:
                found_circular = True
                break
        
        self.assertTrue(found_circular, "未检测到 UIComponent 和 CircularComponent 之间的循环依赖")

    @patch('core.clarifier.architecture_reasoner.run_prompt')
    async def test_integration_with_deep_reasoning(self, mock_run_prompt):
        """测试深度推理过程"""
        mock_run_prompt.side_effect = [
            {
                "overview": {
                    "core_principles": ["分层设计", "关注点分离"],
                    "advantages": ["可维护性", "可扩展性"],
                    "challenges": ["层间通信开销"]
                },
                "layers": {
                    "presentation": {
                        "responsibilities": ["用户界面", "用户交互"],
                        "components": ["UIComponent"]
                    },
                    "business": {
                        "responsibilities": ["业务逻辑", "业务规则"],
                        "components": ["ServiceComponent", "CircularComponent"]
                    },
                    "data": {
                        "responsibilities": ["数据访问", "数据持久化"],
                        "components": ["DataComponent"]
                    }
                },
                "interfaces": {
                    "IUIComponent": {
                        "description": "UI组件接口",
                        "methods": ["render", "handleEvent"]
                    },
                    "IServiceComponent": {
                        "description": "服务组件接口",
                        "methods": ["processData", "validateData"]
                    }
                },
                "dependencies": {
                    "UIComponent": {
                        "depends_on": ["ServiceComponent", "CircularComponent"],
                        "reason": "需要处理业务逻辑"
                    },
                    "ServiceComponent": {
                        "depends_on": ["DataComponent"],
                        "reason": "需要访问数据"
                    }
                }
            },
            {"content": "# 架构概览\n\n## 系统架构概述\n\n本系统采用分层架构设计..."},
            {"content": "# 详细设计\n\n## 模块详情\n\n本系统包含以下模块..."},
            {"content": "# 接口文档\n\n## 接口定义\n\n本系统定义了以下接口..."},
            {"content": "# 部署文档\n\n## 部署要求\n\n本系统的部署要求如下..."}
        ]
        
        architecture_understanding = {
            "architecture_design": {
                "patterns": [
                    {
                        "name": "MVC",
                        "layers": [
                            {
                                "name": "presentation",
                                "components": [
                                    {
                                        "name": "UIComponent",
                                        "description": "UI组件",
                                        "responsibilities": ["显示界面"],
                                        "dependencies": ["ServiceComponent", "CircularComponent"],
                                        "interfaces": ["IUIComponent"],
                                        "features": ["UI渲染"],
                                        "domains": ["前端"],
                                        "technologies": ["React"],
                                        "requirements": ["REQ-001"]
                                    }
                                ]
                            },
                            {
                                "name": "business",
                                "components": [
                                    {
                                        "name": "ServiceComponent",
                                        "description": "服务组件",
                                        "responsibilities": ["处理业务逻辑"],
                                        "dependencies": ["DataComponent"],
                                        "interfaces": ["IServiceComponent"],
                                        "features": ["业务处理"],
                                        "domains": ["业务"],
                                        "technologies": ["Spring"],
                                        "requirements": ["REQ-002"]
                                    },
                                    {
                                        "name": "CircularComponent",
                                        "description": "循环依赖测试组件",
                                        "responsibilities": ["测试循环依赖"],
                                        "dependencies": ["UIComponent"],
                                        "interfaces": ["ICircularComponent"],
                                        "features": ["循环依赖测试"],
                                        "domains": ["测试"],
                                        "technologies": ["Java"],
                                        "requirements": ["REQ-003"]
                                    }
                                ]
                            },
                            {
                                "name": "data",
                                "components": [
                                    {
                                        "name": "DataComponent",
                                        "description": "数据组件",
                                        "responsibilities": ["数据访问"],
                                        "dependencies": [],
                                        "interfaces": ["IDataComponent"],
                                        "features": ["数据访问"],
                                        "domains": ["数据"],
                                        "technologies": ["JPA"],
                                        "requirements": ["REQ-004"]
                                    }
                                ]
                            }
                        ],
                        "interfaces": ["IUIComponent", "IServiceComponent", "IDataComponent", "ICircularComponent"],
                        "dependencies": {
                            "presentation": ["business"],
                            "business": ["data"]
                        }
                    }
                ]
            }
        }
        
        result = await self.reasoner.start_deep_reasoning(architecture_understanding)
        
        self.assertIsNotNone(result)
        self.assertIn("timestamp", result)
        self.assertIn("requirement_module_index", result)
        self.assertIn("responsibility_index", result)
        self.assertIn("dependency_graph", result)
        self.assertIn("layer_index", result)
        
        self.assertTrue((self.output_dir / "01_architecture_overview.md").exists())


if __name__ == '__main__':
    unittest.main()
