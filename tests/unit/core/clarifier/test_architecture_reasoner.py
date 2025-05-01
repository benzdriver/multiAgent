"""
单元测试 - ArchitectureReasoner 类
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import asyncio
from pathlib import Path
import tempfile
import shutil
import os

from core.clarifier.architecture_reasoner import ArchitectureReasoner


class TestArchitectureReasoner(unittest.IsolatedAsyncioTestCase):
    """测试 ArchitectureReasoner 类"""

    async def asyncSetUp(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        
        self.mock_architecture_manager = MagicMock()
        self.mock_architecture_manager.get_architecture_index.return_value = {
            "modules": [],
            "layers": {
                "presentation": {"modules": []},
                "business": {"modules": []},
                "data": {"modules": []}
            }
        }
        
        self.mock_llm_chat = AsyncMock()
        self.mock_llm_chat.return_value = {"result": "模拟的LLM响应"}
        
        self.mock_logger = MagicMock()
        
        self.reasoner = ArchitectureReasoner(
            architecture_manager=self.mock_architecture_manager,
            llm_chat=self.mock_llm_chat,
            logger=self.mock_logger
        )

    async def asyncTearDown(self):
        """测试后的清理"""
        shutil.rmtree(self.temp_dir)

    async def test_init(self):
        """测试初始化"""
        reasoner = ArchitectureReasoner()
        self.assertIsNotNone(reasoner)
        
        reasoner = ArchitectureReasoner(
            architecture_manager=self.mock_architecture_manager,
            llm_chat=self.mock_llm_chat,
            logger=self.mock_logger
        )
        self.assertEqual(reasoner.arch_manager, self.mock_architecture_manager)
        self.assertEqual(reasoner.llm_chat, self.mock_llm_chat)
        self.assertEqual(reasoner.logger, self.mock_logger)

    @patch('core.clarifier.architecture_reasoner.run_prompt')
    async def test_get_llm_response(self, mock_run_prompt):
        """测试获取LLM响应"""
        mock_run_prompt.return_value = {"result": "模拟的LLM响应"}
        
        prompt = "测试提示"
        
        result = await self.reasoner._get_llm_response(prompt)
        
        self.assertEqual(result, {"result": "模拟的LLM响应"})
        mock_run_prompt.assert_called_once()

    @patch('core.clarifier.architecture_reasoner.run_prompt')
    async def test_get_llm_response_error(self, mock_run_prompt):
        """测试获取LLM响应出错的情况"""
        mock_run_prompt.side_effect = Exception("LLM调用失败")
        
        prompt = "测试提示"
        
        result = await self.reasoner._get_llm_response(prompt)
        
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("message", result)
        self.assertIn("LLM调用失败", result["error"])
        mock_run_prompt.assert_called_once()
        self.mock_logger.log.assert_called_with("⚠️ 调用LLM时出错: LLM调用失败", role="error")

    @patch('core.clarifier.architecture_reasoner.run_prompt')
    async def test_get_llm_response_with_run_prompt(self, mock_run_prompt):
        """测试使用run_prompt获取LLM响应"""
        mock_run_prompt.return_value = {"result": "测试结果"}
        
        reasoner = ArchitectureReasoner(
            architecture_manager=self.mock_architecture_manager,
            logger=self.mock_logger
        )
        
        prompt = "测试提示"
        
        result = await reasoner._get_llm_response(prompt)
        
        self.assertEqual(result, {"result": "测试结果"})
        mock_run_prompt.assert_called_once()

    async def test_populate_architecture_index(self):
        """测试填充架构索引"""
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
                                        "dependencies": ["ServiceComponent"],
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
                                    }
                                ]
                            }
                        ],
                        "interfaces": ["IUIComponent", "IServiceComponent"],
                        "dependencies": {
                            "presentation": ["business"],
                            "business": ["data"]
                        }
                    }
                ]
            }
        }
        
        await self.reasoner.populate_architecture_index(architecture_understanding)
        
        self.mock_architecture_manager.index.add_module.assert_called()
        self.assertEqual(self.mock_architecture_manager.index.add_module.call_count, 2)
        
        first_call_args = self.mock_architecture_manager.index.add_module.call_args_list[0]
        self.assertEqual(first_call_args[0][0]["name"], "UIComponent")
        self.assertEqual(first_call_args[0][0]["responsibilities"], ["显示界面"])
        self.assertEqual(first_call_args[0][1], ["REQ-001"])
        
        second_call_args = self.mock_architecture_manager.index.add_module.call_args_list[1]
        self.assertEqual(second_call_args[0][0]["name"], "ServiceComponent")
        self.assertEqual(second_call_args[0][0]["responsibilities"], ["处理业务逻辑"])
        self.assertEqual(second_call_args[0][1], ["REQ-002"])

    @patch.object(ArchitectureReasoner, '_check_naming_inconsistencies')
    @patch.object(ArchitectureReasoner, '_check_layer_violations')
    @patch.object(ArchitectureReasoner, '_check_responsibility_overlaps')
    @patch.object(ArchitectureReasoner, '_check_global_circular_dependencies')
    @patch.object(ArchitectureReasoner, '_check_overall_consistency')
    async def test_check_all_issues(self, mock_consistency, mock_cycles, mock_overlaps, mock_violations, mock_naming):
        """测试检查所有架构问题"""
        mock_naming.return_value = ["命名不一致问题1"]
        mock_violations.return_value = ["层级违规问题1"]
        mock_overlaps.return_value = ["职责重叠问题1"]
        mock_cycles.return_value = ["循环依赖问题1"]
        mock_consistency.return_value = ["一致性问题1"]
        
        result = await self.reasoner.check_all_issues()
        
        self.assertIsNotNone(result)
        self.assertIn("naming_inconsistencies", result)
        self.assertIn("layer_violations", result)
        self.assertIn("responsibility_overlaps", result)
        self.assertIn("circular_dependencies", result)
        self.assertIn("consistency_issues", result)
        
        self.assertEqual(result["naming_inconsistencies"], ["命名不一致问题1"])
        self.assertEqual(result["layer_violations"], ["层级违规问题1"])
        self.assertEqual(result["responsibility_overlaps"], ["职责重叠问题1"])
        self.assertEqual(result["circular_dependencies"], ["循环依赖问题1"])
        self.assertEqual(result["consistency_issues"], ["一致性问题1"])
        
        mock_naming.assert_called_once()
        mock_violations.assert_called_once()
        mock_overlaps.assert_called_once()
        mock_cycles.assert_called_once()
        mock_consistency.assert_called_once()
        
        self.mock_logger.log.assert_any_call("\n🔍 执行全面架构检查...", role="system")
        self.mock_logger.log.assert_any_call("⚠️ 检测到 1 个命名不一致问题", role="error")
        self.mock_logger.log.assert_any_call("⚠️ 检测到 1 个层级违规问题", role="error")
        self.mock_logger.log.assert_any_call("⚠️ 检测到 1 个职责重叠问题", role="error")
        self.mock_logger.log.assert_any_call("⚠️ 检测到 1 个循环依赖问题", role="error")
        self.mock_logger.log.assert_any_call("⚠️ 检测到 1 个一致性问题", role="error")
        self.mock_logger.log.assert_any_call("\n⚠️ 总计检测到 5 个架构问题", role="error")

    @patch.object(ArchitectureReasoner, '_check_naming_inconsistencies')
    @patch.object(ArchitectureReasoner, '_check_layer_violations')
    @patch.object(ArchitectureReasoner, '_check_responsibility_overlaps')
    @patch.object(ArchitectureReasoner, '_check_global_circular_dependencies')
    @patch.object(ArchitectureReasoner, '_check_overall_consistency')
    async def test_check_all_issues_no_issues(self, mock_consistency, mock_cycles, mock_overlaps, mock_violations, mock_naming):
        """测试检查所有架构问题 - 无问题情况"""
        mock_naming.return_value = []
        mock_violations.return_value = []
        mock_overlaps.return_value = []
        mock_cycles.return_value = []
        mock_consistency.return_value = []
        
        result = await self.reasoner.check_all_issues()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["naming_inconsistencies"], [])
        self.assertEqual(result["layer_violations"], [])
        self.assertEqual(result["responsibility_overlaps"], [])
        self.assertEqual(result["circular_dependencies"], [])
        self.assertEqual(result["consistency_issues"], [])
        
        self.mock_logger.log.assert_any_call("✅ 未检测到命名不一致问题", role="system")
        self.mock_logger.log.assert_any_call("✅ 未检测到层级违规", role="system")
        self.mock_logger.log.assert_any_call("✅ 未检测到职责重叠", role="system")
        self.mock_logger.log.assert_any_call("✅ 未检测到循环依赖", role="system")
        self.mock_logger.log.assert_any_call("✅ 未检测到一致性问题", role="system")
        self.mock_logger.log.assert_any_call("\n✅ 架构检查通过，未发现问题", role="system")

    @patch.object(ArchitectureReasoner, '_check_global_circular_dependencies')
    @patch.object(ArchitectureReasoner, '_check_naming_inconsistencies')
    @patch.object(ArchitectureReasoner, '_check_layer_violations')
    @patch.object(ArchitectureReasoner, '_check_responsibility_overlaps')
    async def test_check_module_issues(self, mock_overlaps, mock_violations, mock_naming, mock_cycles):
        """测试检查单个模块的架构问题"""
        mock_cycles.return_value = ["ModuleA -> ModuleB -> ModuleC -> ModuleA", "TestModule -> ModuleD -> TestModule"]
        mock_naming.return_value = ["ModuleA命名不规范", "TestModule命名不规范"]
        mock_violations.return_value = ["ModuleA违反层级规则", "TestModule违反层级规则"]
        mock_overlaps.return_value = ["ModuleA与ModuleB职责重叠", "TestModule与ModuleE职责重叠"]
        
        self.mock_architecture_manager.index.dependency_graph = {
            "TestModule": {"layer": "presentation", "responsibilities": ["测试职责"]},
            "ModuleA": {"layer": "business", "responsibilities": ["业务职责"]}
        }
        
        result = await self.reasoner.check_module_issues("TestModule")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["circular_dependencies"], ["TestModule -> ModuleD -> TestModule"])
        self.assertEqual(result["naming_inconsistencies"], ["TestModule命名不规范"])
        self.assertEqual(result["layer_violations"], ["TestModule违反层级规则"])
        self.assertEqual(result["responsibility_overlaps"], ["TestModule与ModuleE职责重叠"])
        
        self.mock_logger.log.assert_any_call("\n🔍 检查模块 'TestModule' 的架构问题...", role="system")
        self.mock_logger.log.assert_any_call("⚠️ 模块 'TestModule' 参与了 1 个循环依赖", role="error")
        self.mock_logger.log.assert_any_call("⚠️ 模块 'TestModule' 存在 1 个命名问题", role="error")
        self.mock_logger.log.assert_any_call("⚠️ 模块 'TestModule' 存在 1 个层级违规", role="error")
        self.mock_logger.log.assert_any_call("⚠️ 模块 'TestModule' 存在 1 个职责重叠", role="error")
        self.mock_logger.log.assert_any_call("\n⚠️ 模块 'TestModule' 总计存在 4 个架构问题", role="error")

    @patch.object(ArchitectureReasoner, '_check_global_circular_dependencies')
    @patch.object(ArchitectureReasoner, '_check_naming_inconsistencies')
    @patch.object(ArchitectureReasoner, '_check_layer_violations')
    @patch.object(ArchitectureReasoner, '_check_responsibility_overlaps')
    async def test_check_module_issues_no_issues(self, mock_overlaps, mock_violations, mock_naming, mock_cycles):
        """测试检查单个模块的架构问题 - 无问题情况"""
        mock_cycles.return_value = ["ModuleA -> ModuleB -> ModuleC -> ModuleA"]
        mock_naming.return_value = ["ModuleA命名不规范"]
        mock_violations.return_value = ["ModuleA违反层级规则"]
        mock_overlaps.return_value = ["ModuleA与ModuleB职责重叠"]
        
        self.mock_architecture_manager.index.dependency_graph = {
            "TestModule": {"layer": "presentation", "responsibilities": ["测试职责"]},
            "ModuleA": {"layer": "business", "responsibilities": ["业务职责"]}
        }
        
        result = await self.reasoner.check_module_issues("TestModule")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["circular_dependencies"], [])
        self.assertEqual(result["naming_inconsistencies"], [])
        self.assertEqual(result["layer_violations"], [])
        self.assertEqual(result["responsibility_overlaps"], [])
        
        self.mock_logger.log.assert_any_call("✅ 模块 'TestModule' 未参与循环依赖", role="system")
        self.mock_logger.log.assert_any_call("✅ 模块 'TestModule' 命名符合规范", role="system")
        self.mock_logger.log.assert_any_call("✅ 模块 'TestModule' 未违反层级规则", role="system")
        self.mock_logger.log.assert_any_call("✅ 模块 'TestModule' 职责明确，无重叠", role="system")
        self.mock_logger.log.assert_any_call("\n✅ 模块 'TestModule' 架构检查通过，未发现问题", role="system")

    @patch.object(ArchitectureReasoner, '_check_global_circular_dependencies')
    @patch.object(ArchitectureReasoner, '_check_naming_inconsistencies')
    @patch.object(ArchitectureReasoner, '_check_layer_violations')
    @patch.object(ArchitectureReasoner, '_check_responsibility_overlaps')
    async def test_check_module_issues_module_not_exist(self, mock_overlaps, mock_violations, mock_naming, mock_cycles):
        """测试检查不存在的模块"""
        self.mock_architecture_manager.index.dependency_graph = {
            "ModuleA": {"layer": "business", "responsibilities": ["业务职责"]}
        }
        
        result = await self.reasoner.check_module_issues("TestModule")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["circular_dependencies"], [])
        self.assertEqual(result["naming_inconsistencies"], [])
        self.assertEqual(result["layer_violations"], [])
        self.assertEqual(result["responsibility_overlaps"], [])
        
        self.mock_logger.log.assert_any_call("❌ 模块 'TestModule' 不存在", role="error")
        
        mock_cycles.assert_not_called()
        mock_naming.assert_not_called()
        mock_violations.assert_not_called()
        mock_overlaps.assert_not_called()

    @patch.object(ArchitectureReasoner, 'populate_architecture_index')
    @patch.object(ArchitectureReasoner, '_generate_pattern_docs')
    @patch.object(ArchitectureReasoner, '_reason_by_pattern')
    @patch.object(ArchitectureReasoner, '_validate_overall_architecture')
    @patch.object(ArchitectureReasoner, '_save_final_architecture')
    async def test_start_deep_reasoning(self, mock_save, mock_validate, mock_reason, mock_generate, mock_populate):
        """测试开始架构深度推理过程"""
        mock_populate.return_value = None
        mock_generate.return_value = {"overview": {}, "layers": {}, "interfaces": {}, "dependencies": {}}
        mock_reason.return_value = None
        mock_validate.return_value = None
        mock_save.return_value = None
        
        self.mock_architecture_manager.index.get_current_state.return_value = {
            "modules": [{"name": "TestModule", "layer": "presentation"}],
            "layers": {"presentation": {"modules": ["TestModule"]}}
        }
        
        architecture_understanding = {
            "architecture_design": {
                "patterns": [
                    {
                        "name": "MVC",
                        "layers": [
                            {"name": "presentation", "components": [{"name": "UIComponent"}]},
                            {"name": "business", "components": [{"name": "ServiceComponent"}]}
                        ],
                        "interfaces": [],
                        "dependencies": {}
                    }
                ]
            }
        }
        
        result = await self.reasoner.start_deep_reasoning(architecture_understanding)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, self.mock_architecture_manager.index.get_current_state.return_value)
        
        mock_populate.assert_called_once_with(architecture_understanding)
        mock_generate.assert_called_once()
        mock_reason.assert_called_once()
        mock_validate.assert_called_once()
        mock_save.assert_called_once()
        
        self.mock_logger.log.assert_any_call("\n🏗️ 开始架构深度推理...", role="system")

    @patch.object(ArchitectureReasoner, 'populate_architecture_index')
    @patch.object(ArchitectureReasoner, '_generate_pattern_docs')
    @patch.object(ArchitectureReasoner, '_reason_by_pattern')
    @patch.object(ArchitectureReasoner, '_validate_overall_architecture')
    @patch.object(ArchitectureReasoner, '_save_final_architecture')
    async def test_start_deep_reasoning_with_custom_llm(self, mock_save, mock_validate, mock_reason, mock_generate, mock_populate):
        """测试使用自定义LLM响应函数进行架构深度推理"""
        mock_populate.return_value = None
        mock_generate.return_value = {"overview": {}, "layers": {}, "interfaces": {}, "dependencies": {}}
        mock_reason.return_value = None
        mock_validate.return_value = None
        mock_save.return_value = None
        
        self.mock_architecture_manager.index.get_current_state.return_value = {
            "modules": [{"name": "TestModule", "layer": "presentation"}],
            "layers": {"presentation": {"modules": ["TestModule"]}}
        }
        
        architecture_understanding = {
            "architecture_design": {
                "patterns": [
                    {
                        "name": "MVC",
                        "layers": [
                            {"name": "presentation", "components": [{"name": "UIComponent"}]},
                            {"name": "business", "components": [{"name": "ServiceComponent"}]}
                        ],
                        "interfaces": [],
                        "dependencies": {}
                    }
                ]
            }
        }
        
        custom_llm = AsyncMock()
        custom_llm.return_value = {"custom": "response"}
        
        result = await self.reasoner.start_deep_reasoning(architecture_understanding, get_llm_response=custom_llm)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, self.mock_architecture_manager.index.get_current_state.return_value)
        
        mock_populate.assert_called_once_with(architecture_understanding)
        mock_generate.assert_called_once()
        mock_reason.assert_called_once()
        mock_validate.assert_called_once()
        mock_save.assert_called_once()
        
        self.assertEqual(self.reasoner._get_llm_response, custom_llm)


if __name__ == '__main__':
    unittest.main()
