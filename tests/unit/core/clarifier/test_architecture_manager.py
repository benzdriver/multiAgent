import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
from datetime import datetime

from core.clarifier.architecture_manager import ArchitectureIndex, ArchitectureValidator, ArchitectureManager

class TestArchitectureIndex:
    """ArchitectureIndex 单元测试"""
    
    def test_init(self):
        """测试初始化是否正确设置属性"""
        index = ArchitectureIndex()
        
        assert isinstance(index.requirement_module_index, dict)
        assert isinstance(index.responsibility_index, dict)
        assert isinstance(index.dependency_graph, dict)
        assert isinstance(index.keyword_mapping, dict)
        assert isinstance(index.layer_index, dict)
        
        assert "frontend" in index.architecture_patterns
        assert "backend" in index.architecture_patterns
        assert "fullstack" in index.architecture_patterns
        
        assert "frontend.pages" in index.layer_index
        assert "backend.controllers" in index.layer_index
        assert "fullstack.features" in index.layer_index
    
    def test_add_module(self):
        """测试添加模块到索引"""
        index = ArchitectureIndex()
        
        module = {
            "name": "TestModule",
            "responsibilities": ["测试责任1", "测试责任2"],
            "dependencies": ["ModuleA", "ModuleB"],
            "pattern": "frontend",
            "layer": "components",
            "description": "这是一个测试模块 关键字1 关键字2"
        }
        
        requirements = ["需求1", "需求2"]
        
        index.add_module(module, requirements)
        
        assert "需求1" in index.requirement_module_index
        assert "需求2" in index.requirement_module_index
        assert "TestModule" in index.requirement_module_index["需求1"]
        assert "TestModule" in index.requirement_module_index["需求2"]
        
        assert "测试责任1" in index.responsibility_index
        assert "测试责任2" in index.responsibility_index
        assert "TestModule" in index.responsibility_index["测试责任1"]["modules"]
        assert "frontend" in index.responsibility_index["测试责任1"]["patterns"]
        
        assert "TestModule" in index.dependency_graph
        assert "ModuleA" in index.dependency_graph["TestModule"]["depends_on"]
        assert "ModuleB" in index.dependency_graph["TestModule"]["depends_on"]
        assert "frontend" == index.dependency_graph["TestModule"]["pattern"]
        assert "components" == index.dependency_graph["TestModule"]["layer"]
        
        assert "这是一个测试模块" in index.keyword_mapping
        assert "关键字1" in index.keyword_mapping
        assert "关键字2" in index.keyword_mapping
        assert "TestModule" in index.keyword_mapping["关键字1"]
        
        assert "TestModule" in index.layer_index["frontend.components"]
    
    def test_extract_keywords(self):
        """测试从文本中提取关键字"""
        index = ArchitectureIndex()
        
        text = "这是一个测试文本 包含关键字1 和 关键字2"
        keywords = index._extract_keywords(text)
        
        assert "这是一个测试文本" in keywords
        assert "包含关键字1" in keywords
        assert "和" in keywords
        assert "关键字2" in keywords
    
    def test_get_allowed_dependencies(self):
        """测试获取特定架构模式和层级允许的依赖"""
        index = ArchitectureIndex()
        
        frontend_pages_deps = index.get_allowed_dependencies("frontend", "pages")
        assert "components" in frontend_pages_deps
        assert "layouts" in frontend_pages_deps
        assert "hooks" in frontend_pages_deps
        assert "stores" in frontend_pages_deps
        
        backend_controllers_deps = index.get_allowed_dependencies("backend", "controllers")
        assert "services" in backend_controllers_deps
        assert "repositories" not in backend_controllers_deps
        
        nonexistent_deps = index.get_allowed_dependencies("nonexistent", "layer")
        assert nonexistent_deps == []
    
    def test_get_layer_path(self):
        """测试获取特定架构模式和层级的文件路径"""
        index = ArchitectureIndex()
        
        frontend_components_path = index.get_layer_path("frontend", "components")
        assert frontend_components_path == "src/components"
        
        backend_services_path = index.get_layer_path("backend", "services")
        assert backend_services_path == "src/services"
        
        nonexistent_path = index.get_layer_path("nonexistent", "layer")
        assert nonexistent_path == ""
        
        nonexistent_layer_path = index.get_layer_path("frontend", "nonexistent")
        assert nonexistent_layer_path == ""


class TestArchitectureValidator:
    """ArchitectureValidator 单元测试"""
    
    @pytest.fixture
    def setup_validator(self):
        """设置测试环境"""
        index = ArchitectureIndex()
        
        existing_module1 = {
            "name": "ExistingModule1",
            "responsibilities": ["职责1", "职责2"],
            "dependencies": [],
            "pattern": "frontend",
            "layer": "components"
        }
        
        existing_module2 = {
            "name": "ExistingModule2",
            "responsibilities": ["职责3"],
            "dependencies": ["ExistingModule1"],
            "pattern": "frontend",
            "layer": "pages"
        }
        
        index.add_module(existing_module1, ["需求1"])
        index.add_module(existing_module2, ["需求2"])
        
        validator = ArchitectureValidator(index)
        
        return {
            "index": index,
            "validator": validator,
            "existing_module1": existing_module1,
            "existing_module2": existing_module2
        }
    
    def test_init(self, setup_validator):
        """测试初始化是否正确设置属性"""
        validator = setup_validator["validator"]
        
        assert validator.index == setup_validator["index"]
        assert isinstance(validator.validation_issues, dict)
    
    @pytest.mark.asyncio
    async def test_validate_new_module_no_issues(self, setup_validator):
        """测试验证没有问题的新模块"""
        validator = setup_validator["validator"]
        
        new_module = {
            "name": "NewModule",
            "responsibilities": ["新职责1", "新职责2"],
            "dependencies": ["ExistingModule1"],
            "pattern": "frontend",
            "layer": "pages"
        }
        
        requirements = ["需求3"]
        
        with patch.object(validator, '_check_responsibility_overlaps', return_value=[]), \
             patch.object(validator, '_check_circular_dependencies', return_value=[]), \
             patch.object(validator, '_check_layer_violations', return_value=[]):
            
            issues = await validator.validate_new_module(new_module, requirements)
            
            assert issues["responsibility_overlaps"] == []
            assert issues["circular_dependencies"] == []
            assert issues["layer_violations"] == []
            assert "NewModule" in validator.validation_issues
    
    @pytest.mark.asyncio
    async def test_validate_new_module_with_issues(self, setup_validator):
        """测试验证有问题的新模块"""
        validator = setup_validator["validator"]
        
        new_module = {
            "name": "NewModule",
            "responsibilities": ["职责1", "新职责2"],  # 职责1 与 ExistingModule1 重叠
            "dependencies": ["ExistingModule2", "NewModule"],  # 循环依赖
            "pattern": "frontend",
            "layer": "hooks"  # 层级违规
        }
        
        requirements = ["需求3"]
        
        responsibility_overlaps = ["职责'职责1'与模块{'ExistingModule1'}重叠"]
        circular_dependencies = ["NewModule -> ExistingModule2 -> ExistingModule1 -> NewModule"]
        layer_violations = ["依赖 'ExistingModule2' 违反了 'frontend' 架构中 'hooks' 层级的依赖规则"]
        
        with patch.object(validator, '_check_responsibility_overlaps', return_value=responsibility_overlaps), \
             patch.object(validator, '_check_circular_dependencies', return_value=circular_dependencies), \
             patch.object(validator, '_check_layer_violations', return_value=layer_violations):
            
            issues = await validator.validate_new_module(new_module, requirements)
            
            assert issues["responsibility_overlaps"] == responsibility_overlaps
            assert issues["circular_dependencies"] == circular_dependencies
            assert issues["layer_violations"] == layer_violations
            assert "NewModule" in validator.validation_issues
    
    def test_get_validation_issues(self, setup_validator):
        """测试获取所有验证问题"""
        validator = setup_validator["validator"]
        
        validator.validation_issues = {
            "Module1": {
                "responsibility_overlaps": ["问题1"],
                "circular_dependencies": [],
                "layer_violations": []
            },
            "Module2": {
                "responsibility_overlaps": [],
                "circular_dependencies": ["问题2"],
                "layer_violations": []
            },
            "Module3": {
                "responsibility_overlaps": [],
                "circular_dependencies": [],
                "layer_violations": []
            }
        }
        
        issues = validator.get_validation_issues()
        
        assert "Module1" in issues
        assert "Module2" in issues
        assert "Module3" not in issues  # 没有问题的模块不应该返回
        assert issues["Module1"]["responsibility_overlaps"] == ["问题1"]
        assert issues["Module2"]["circular_dependencies"] == ["问题2"]
    
    def test_check_responsibility_overlaps(self, setup_validator):
        """测试检查职责重叠"""
        validator = setup_validator["validator"]
        
        module_with_overlaps = {
            "name": "TestModule",
            "responsibilities": ["职责1", "新职责"]  # 职责1 与 ExistingModule1 重叠
        }
        
        overlaps = validator._check_responsibility_overlaps(module_with_overlaps)
        assert len(overlaps) == 1
        assert "职责'职责1'" in overlaps[0]
        assert "ExistingModule1" in overlaps[0]
        
        module_without_overlaps = {
            "name": "TestModule",
            "responsibilities": ["新职责1", "新职责2"]
        }
        
        overlaps = validator._check_responsibility_overlaps(module_without_overlaps)
        assert len(overlaps) == 0
    
    def test_check_circular_dependencies(self, setup_validator):
        """测试检查循环依赖"""
        validator = setup_validator["validator"]
        
        module_with_cycle = {
            "name": "TestModule",
            "dependencies": ["ExistingModule2"]  # 形成循环: TestModule -> ExistingModule2 -> ExistingModule1 -> TestModule
        }
        
        validator.index.dependency_graph["ExistingModule1"]["depends_on"].add("TestModule")
        
        cycles = validator._check_circular_dependencies(module_with_cycle)
        
        validator.index.dependency_graph["ExistingModule1"]["depends_on"].remove("TestModule")
        
        assert len(cycles) == 1
        
        module_without_cycle = {
            "name": "TestModule",
            "dependencies": ["ExistingModule1"]
        }
        
        cycles = validator._check_circular_dependencies(module_without_cycle)
        assert len(cycles) == 0
    
    def test_check_layer_violations(self, setup_validator):
        """测试检查层级违规"""
        validator = setup_validator["validator"]
        
        module_with_violations = {
            "name": "TestModule",
            "dependencies": ["ExistingModule1"],
            "pattern": "backend",
            "layer": "models"  # 后端模型层不应该依赖前端组件
        }
        
        violations = validator._check_layer_violations(module_with_violations)
        
        assert len(violations) == 1
        assert "ExistingModule1" in violations[0]
        assert "backend" in violations[0]
        assert "models" in violations[0]
        
        module_without_violations = {
            "name": "TestModule",
            "dependencies": ["ExistingModule1"],
            "pattern": "frontend",
            "layer": "pages"  # 前端页面可以依赖前端组件
        }
        
        violations = validator._check_layer_violations(module_without_violations)
        assert len(violations) == 0


class TestArchitectureManager:
    """ArchitectureManager 单元测试"""
    
    @pytest.fixture
    def setup_manager(self):
        """设置测试环境"""
        with patch('pathlib.Path.mkdir'):
            manager = ArchitectureManager()
            return manager
    
    def test_init(self, setup_manager):
        """测试初始化是否正确设置属性"""
        manager = setup_manager
        
        assert isinstance(manager.index, ArchitectureIndex)
        assert isinstance(manager.validator, ArchitectureValidator)
        assert manager.output_path == Path("data/output/architecture")
        assert isinstance(manager.modules, list)
        assert isinstance(manager.requirements, list)
        assert isinstance(manager.system_overview, dict)
        assert isinstance(manager.functional_requirements, dict)
        assert isinstance(manager.technology_stack, dict)
        assert isinstance(manager.architecture_pattern, dict)
    
    def test_get_validation_issues(self, setup_manager):
        """测试获取所有架构验证问题"""
        manager = setup_manager
        
        mock_issues = {
            "Module1": {
                "responsibility_overlaps": ["问题1"],
                "circular_dependencies": [],
                "layer_violations": []
            }
        }
        
        with patch.object(manager.validator, 'get_validation_issues', return_value=mock_issues):
            issues = manager.get_validation_issues()
            
            assert issues == mock_issues
            assert "Module1" in issues
            assert issues["Module1"]["responsibility_overlaps"] == ["问题1"]
    
    def test_add_module_new(self, setup_manager):
        """测试添加新模块"""
        manager = setup_manager
        
        module_data = {
            "name": "TestModule",
            "responsibilities": ["职责1", "职责2"],
            "dependencies": []
        }
        
        manager.add_module(module_data)
        
        assert len(manager.modules) == 1
        assert manager.modules[0] == module_data
    
    def test_add_module_update(self, setup_manager):
        """测试更新现有模块"""
        manager = setup_manager
        
        original_module = {
            "name": "TestModule",
            "responsibilities": ["职责1"],
            "dependencies": []
        }
        
        manager.add_module(original_module)
        
        updated_module = {
            "name": "TestModule",
            "responsibilities": ["职责1", "职责2"],
            "dependencies": ["ModuleA"]
        }
        
        manager.add_module(updated_module)
        
        assert len(manager.modules) == 1
        assert manager.modules[0] == updated_module
        assert manager.modules[0]["responsibilities"] == ["职责1", "职责2"]
        assert manager.modules[0]["dependencies"] == ["ModuleA"]
    
    def test_add_requirement_new(self, setup_manager):
        """测试添加新需求"""
        manager = setup_manager
        
        req_data = {
            "id": "REQ-001",
            "description": "测试需求",
            "priority": "高"
        }
        
        manager.add_requirement(req_data)
        
        assert len(manager.requirements) == 1
        assert manager.requirements[0] == req_data
    
    def test_add_requirement_update(self, setup_manager):
        """测试更新现有需求"""
        manager = setup_manager
        
        original_req = {
            "id": "REQ-001",
            "description": "测试需求",
            "priority": "中"
        }
        
        manager.add_requirement(original_req)
        
        updated_req = {
            "id": "REQ-001",
            "description": "更新后的测试需求",
            "priority": "高"
        }
        
        manager.add_requirement(updated_req)
        
        assert len(manager.requirements) == 1
        assert manager.requirements[0] == updated_req
        assert manager.requirements[0]["description"] == "更新后的测试需求"
        assert manager.requirements[0]["priority"] == "高"
    
    def test_add_requirement_auto_id(self, setup_manager):
        """测试自动生成需求ID"""
        manager = setup_manager
        
        req_data = {
            "description": "测试需求",
            "priority": "高"
        }
        
        manager.add_requirement(req_data)
        
        assert len(manager.requirements) == 1
        assert "id" in manager.requirements[0]
        assert manager.requirements[0]["id"] == "req_1"
    
    @pytest.mark.asyncio
    async def test_process_new_module_validation_failed(self, setup_manager):
        """测试处理验证失败的新模块"""
        manager = setup_manager
        
        module_spec = {
            "name": "TestModule",
            "responsibilities": ["职责1", "职责2"],
            "dependencies": []
        }
        
        requirements = ["需求1", "需求2"]
        
        validation_issues = {
            "responsibility_overlaps": ["问题1"],
            "circular_dependencies": [],
            "layer_violations": []
        }
        
        with patch.object(manager.validator, 'validate_new_module', return_value=validation_issues):
            result = await manager.process_new_module(module_spec, requirements)
            
            assert result["status"] == "validation_failed"
            assert result["issues"] == validation_issues
    
    @pytest.mark.asyncio
    async def test_process_new_module_success(self, setup_manager):
        """测试处理验证成功的新模块"""
        manager = setup_manager
        
        module_spec = {
            "name": "TestModule",
            "responsibilities": ["职责1", "职责2"],
            "dependencies": []
        }
        
        requirements = ["需求1", "需求2"]
        
        validation_issues = {
            "responsibility_overlaps": [],
            "circular_dependencies": [],
            "layer_violations": []
        }
        
        with patch.object(manager.validator, 'validate_new_module', return_value=validation_issues), \
             patch.object(manager.index, 'add_module'), \
             patch.object(manager, 'add_module'), \
             patch.object(manager, '_save_architecture_state'), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            result = await manager.process_new_module(module_spec, requirements)
            
            assert result["status"] == "success"
            assert result["module"] == module_spec
            
            manager.index.add_module.assert_called_once_with(module_spec, requirements)
            manager.add_module.assert_called_once_with(module_spec)
            manager._save_architecture_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_new_module_file_error(self, setup_manager):
        """测试处理文件操作错误"""
        manager = setup_manager
        
        module_spec = {
            "name": "TestModule",
            "responsibilities": ["职责1", "职责2"],
            "dependencies": []
        }
        
        requirements = ["需求1", "需求2"]
        
        validation_issues = {
            "responsibility_overlaps": [],
            "circular_dependencies": [],
            "layer_violations": []
        }
        
        with patch.object(manager.validator, 'validate_new_module', return_value=validation_issues), \
             patch.object(manager.index, 'add_module'), \
             patch.object(manager, 'add_module'), \
             patch.object(manager, '_save_architecture_state'), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', side_effect=Exception("文件操作错误")):
            
            result = await manager.process_new_module(module_spec, requirements)
            
            assert result["status"] == "success"
            assert result["module"] == module_spec
            
            manager.index.add_module.assert_called_once_with(module_spec, requirements)
            manager.add_module.assert_called_once_with(module_spec)
            manager._save_architecture_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_architecture_state(self, setup_manager):
        """测试保存架构状态"""
        manager = setup_manager
        
        manager.index.requirement_module_index = {
            "需求1": {"模块1", "模块2"},
            "需求2": {"模块3"}
        }
        
        manager.index.responsibility_index = {
            "职责1": {
                "modules": {"模块1"},
                "objects": {"对象1"},
                "patterns": {"前端"}
            }
        }
        
        manager.index.dependency_graph = {
            "模块1": {
                "depends_on": {"模块2"},
                "depended_by": {"模块3"},
                "pattern": "前端",
                "layer": "组件"
            }
        }
        
        manager.index.layer_index = {
            "前端.组件": {
                "模块1": {"name": "模块1"}
            }
        }
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            await manager._save_architecture_state()
            
            mock_file.assert_called_once_with(
                manager.output_path / "architecture_state.json",
                'w',
                encoding='utf-8'
            )
            
            args, kwargs = mock_json_dump.call_args
            state = args[0]
            
            assert "timestamp" in state
            assert state["requirement_module_index"]["需求1"] == ["模块1", "模块2"]
            assert state["responsibility_index"]["职责1"]["modules"] == ["模块1"]
            assert state["dependency_graph"]["模块1"]["depends_on"] == ["模块2"]
            assert state["layer_index"]["前端.组件"]["模块1"] == {"name": "模块1"}
