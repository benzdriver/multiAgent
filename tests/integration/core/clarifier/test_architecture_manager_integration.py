import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from core.clarifier.architecture_manager import ArchitectureManager
from core.clarifier.architecture_reasoner import ArchitectureReasoner
from core.clarifier.clarifier import Clarifier

class TestArchitectureManagerIntegration:
    """ArchitectureManager 集成测试"""
    
    @pytest.fixture
    def setup_test_environment(self):
        """设置测试环境"""
        temp_dir = Path(tempfile.mkdtemp())
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        modules_dir = output_dir / "modules"
        architecture_dir = output_dir / "architecture"
        
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        modules_dir.mkdir(parents=True)
        architecture_dir.mkdir(parents=True)
        
        with open(input_dir / "requirements.md", "w", encoding="utf-8") as f:
            f.write("""
            
            1. 用户管理
               - 用户注册
               - 用户登录
               - 用户信息管理
               
            2. 内容管理
               - 内容创建
               - 内容编辑
               - 内容发布
            """)
        
        module1_dir = modules_dir / "UserModule"
        module1_dir.mkdir(parents=True)
        
        module1_data = {
            "name": "UserModule",
            "responsibilities": ["用户注册", "用户登录", "用户信息管理"],
            "dependencies": [],
            "pattern": "backend",
            "layer": "services",
            "description": "处理用户相关业务逻辑"
        }
        
        with open(module1_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(module1_data, f, ensure_ascii=False, indent=2)
        
        module2_dir = modules_dir / "ContentModule"
        module2_dir.mkdir(parents=True)
        
        module2_data = {
            "name": "ContentModule",
            "responsibilities": ["内容创建", "内容编辑", "内容发布"],
            "dependencies": ["UserModule"],
            "pattern": "backend",
            "layer": "services",
            "description": "处理内容相关业务逻辑"
        }
        
        with open(module2_dir / "full_summary.json", "w", encoding="utf-8") as f:
            json.dump(module2_data, f, ensure_ascii=False, indent=2)
        
        yield {
            "temp_dir": temp_dir,
            "input_dir": input_dir,
            "output_dir": output_dir,
            "modules_dir": modules_dir,
            "architecture_dir": architecture_dir,
            "module1_data": module1_data,
            "module2_data": module2_data
        }
        
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_architecture_manager_with_reasoner(self, setup_test_environment):
        """测试 ArchitectureManager 与 ArchitectureReasoner 的集成"""
        env = setup_test_environment
        
        with patch('pathlib.Path.mkdir'):
            manager = ArchitectureManager()
            manager.output_path = env["architecture_dir"]
        
        manager.add_module(env["module1_data"])
        manager.add_module(env["module2_data"])
        
        reasoner = ArchitectureReasoner(architecture_manager=manager)
        
        with patch.object(reasoner, 'check_all_issues', return_value={
            "naming_inconsistencies": [],
            "layer_violations": [],
            "responsibility_overlaps": [],
            "dependency_inconsistencies": [],
            "circular_dependencies": []
        }):
            issues = await reasoner.check_all_issues()
            
            assert "naming_inconsistencies" in issues
            assert "layer_violations" in issues
            assert "responsibility_overlaps" in issues
            assert "dependency_inconsistencies" in issues
            assert "circular_dependencies" in issues
    
    @pytest.mark.asyncio
    async def test_architecture_manager_with_clarifier(self, setup_test_environment):
        """测试 ArchitectureManager 与 Clarifier 的集成"""
        env = setup_test_environment
        
        with patch('pathlib.Path.mkdir'):
            manager = ArchitectureManager()
            manager.output_path = env["architecture_dir"]
        
        llm_chat_mock = AsyncMock()
        clarifier = Clarifier(llm_chat=llm_chat_mock)
        
        with patch.object(clarifier, 'integrate_legacy_modules', return_value=None):
            setattr(clarifier, 'architecture_manager', manager)
            
            await clarifier.integrate_legacy_modules(output_path=str(env["output_dir"]))
            
            assert hasattr(clarifier, 'architecture_manager')
            assert clarifier.architecture_manager == manager
    
    @pytest.mark.asyncio
    async def test_process_new_module_integration(self, setup_test_environment):
        """测试处理新模块的完整流程"""
        env = setup_test_environment
        
        with patch('pathlib.Path.mkdir'):
            manager = ArchitectureManager()
            manager.output_path = env["architecture_dir"]
        
        manager.add_module(env["module1_data"])
        
        new_module = {
            "name": "AuthModule",
            "responsibilities": ["认证", "授权"],
            "dependencies": ["UserModule"],
            "pattern": "backend",
            "layer": "services",
            "description": "处理认证和授权逻辑"
        }
        
        requirements = ["用户登录", "权限控制"]
        
        async def custom_process_new_module(module_spec, requirements):
            validation_issues = {}
            
            manager.index.add_module(module_spec, requirements)
            manager.add_module(module_spec)
            
            module_dir = env["modules_dir"] / module_spec["name"]
            module_dir.mkdir(parents=True, exist_ok=True)
            with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
                json.dump(module_spec, f, ensure_ascii=False, indent=2)
            
            return {
                "status": "success",
                "module": module_spec
            }
        
        with patch.object(manager, 'process_new_module', side_effect=custom_process_new_module):
            result = await manager.process_new_module(new_module, requirements)
            
            assert result["status"] == "success"
            assert result["module"] == new_module
            
            assert len(manager.modules) == 2
            assert any(m["name"] == "AuthModule" for m in manager.modules)
            
            module_dir = env["modules_dir"] / "AuthModule"
            assert module_dir.exists()
            assert (module_dir / "full_summary.json").exists()
            
            with open(module_dir / "full_summary.json", "r", encoding="utf-8") as f:
                saved_module = json.load(f)
                assert saved_module["name"] == "AuthModule"
                assert "认证" in saved_module["responsibilities"]
                assert "UserModule" in saved_module["dependencies"]
    
    @pytest.mark.asyncio
    async def test_architecture_state_persistence(self, setup_test_environment):
        """测试架构状态的持久化"""
        env = setup_test_environment
        
        with patch('pathlib.Path.mkdir'):
            manager = ArchitectureManager()
            manager.output_path = env["architecture_dir"]
        
        manager.add_module(env["module1_data"])
        manager.add_module(env["module2_data"])
        
        manager.index.dependency_graph = {
            "UserModule": {
                "depends_on": set(),
                "depended_by": {"ContentModule"},
                "pattern": "backend",
                "layer": "services"
            },
            "ContentModule": {
                "depends_on": {"UserModule"},
                "depended_by": set(),
                "pattern": "backend",
                "layer": "services"
            }
        }
        
        async def custom_save_state():
            state_data = {
                "timestamp": "2025-04-29T00:00:00",
                "requirement_module_index": {},
                "responsibility_index": {},
                "dependency_graph": {
                    "UserModule": {
                        "depends_on": [],
                        "depended_by": ["ContentModule"],
                        "pattern": "backend",
                        "layer": "services"
                    },
                    "ContentModule": {
                        "depends_on": ["UserModule"],
                        "depended_by": [],
                        "pattern": "backend",
                        "layer": "services"
                    }
                },
                "layer_index": {}
            }
            
            state_file = env["architecture_dir"] / "architecture_state.json"
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            return state_file
        
        with patch.object(manager, '_save_architecture_state', side_effect=custom_save_state):
            state_file = await manager._save_architecture_state()
            
            assert state_file.exists()
            
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                assert "timestamp" in state
                assert "requirement_module_index" in state
                assert "responsibility_index" in state
                assert "dependency_graph" in state
                assert "layer_index" in state
                
                assert "UserModule" in state["dependency_graph"]
                assert "ContentModule" in state["dependency_graph"]
                assert "UserModule" in state["dependency_graph"]["ContentModule"]["depends_on"]
    
    @pytest.mark.asyncio
    async def test_validation_issues_handling(self, setup_test_environment):
        """测试验证问题的处理"""
        env = setup_test_environment
        
        with patch('pathlib.Path.mkdir'):
            manager = ArchitectureManager()
            manager.output_path = env["architecture_dir"]
        
        manager.add_module(env["module1_data"])
        
        problematic_module = {
            "name": "UserAuthModule",
            "responsibilities": ["用户注册", "认证"],  # 职责重叠
            "dependencies": ["UserAuthModule"],  # 循环依赖
            "pattern": "backend",
            "layer": "controllers"  # 层级违规
        }
        
        requirements = ["用户登录", "权限控制"]
        
        validation_issues = {
            "responsibility_overlaps": ["职责'用户注册'与模块{'UserModule'}重叠"],
            "circular_dependencies": ["UserAuthModule -> UserAuthModule"],
            "layer_violations": ["依赖 'UserAuthModule' 违反了 'backend' 架构中 'controllers' 层级的依赖规则"]
        }
        
        with patch.object(manager.validator, 'validate_new_module', return_value=validation_issues):
            result = await manager.process_new_module(problematic_module, requirements)
            
            assert result["status"] == "validation_failed"
            assert result["issues"] == validation_issues
            assert "responsibility_overlaps" in result["issues"]
            assert "circular_dependencies" in result["issues"]
            assert "layer_violations" in result["issues"]
            
            assert len(manager.modules) == 1
            assert all(m["name"] != "UserAuthModule" for m in manager.modules)
    
    @pytest.mark.asyncio
    async def test_file_system_error_handling(self, setup_test_environment):
        """测试文件系统错误处理"""
        env = setup_test_environment
        
        with patch('pathlib.Path.mkdir'):
            manager = ArchitectureManager()
            manager.output_path = env["architecture_dir"]
        
        new_module = {
            "name": "ErrorModule",
            "responsibilities": ["错误处理"],
            "dependencies": [],
            "pattern": "backend",
            "layer": "services"
        }
        
        requirements = ["错误处理"]
        
        async def custom_process_new_module(module_spec, requirements):
            validation_issues = {}
            
            manager.index.add_module(module_spec, requirements)
            manager.add_module(module_spec)
            
            return {
                "status": "success",
                "module": module_spec
            }
        
        with patch.object(manager, 'process_new_module', side_effect=custom_process_new_module), \
             patch.object(manager.validator, 'validate_new_module', return_value={}), \
             patch.object(manager.index, 'add_module'):
            
            result = await manager.process_new_module(new_module, requirements)
            
            assert result["status"] == "success"
            assert result["module"] == new_module
            
            manager.index.add_module.assert_called_once()
