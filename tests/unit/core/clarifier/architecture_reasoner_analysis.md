# architecture_reasoner.py 模块分析

## 模块概述
architecture_reasoner.py 是 core/clarifier 包中的核心组件，负责对架构进行深度推理、验证和问题检测。该模块使用 LLM 进行架构文档生成和问题修正，并与 ArchitectureManager 交互来管理架构状态。

## 类和方法

### ArchitectureReasoner
主要类，提供架构推理和验证功能。

**初始化方法：**
- `__init__(architecture_manager=None, llm_chat=None, logger=None)`: 初始化推理器，可选择性地提供架构管理器、LLM 聊天接口和日志记录器。

**主要公共方法：**
- `populate_architecture_index(architecture_understanding)`: 将架构理解数据填充到架构索引中
- `start_deep_reasoning(architecture_understanding, get_llm_response=None)`: 开始架构深度推理过程
- `check_all_issues()`: 检查所有架构问题，包括循环依赖、命名不一致性、层级违规、职责重叠和整体一致性
- `check_module_issues(module_name)`: 检查单个模块的架构问题

**架构问题检测方法：**
- `_check_naming_inconsistencies()`: 检查命名不一致性
- `_check_layer_violations()`: 检查层级违规
- `_check_responsibility_overlaps()`: 检查职责重叠
- `_check_global_circular_dependencies()`: 检查全局循环依赖
- `_check_overall_consistency()`: 检查整体架构一致性

**架构文档生成方法：**
- `_generate_architecture_docs()`: 生成架构文档
- `_generate_overview_doc(arch_state)`: 生成架构概览文档
- `_generate_detailed_design_doc(arch_state)`: 生成详细设计文档
- `_generate_interface_doc(arch_state)`: 生成接口文档
- `_generate_deployment_doc(arch_state)`: 生成部署文档

**架构问题修正方法：**
- `_attempt_consistency_correction(issues)`: 尝试自动修正架构一致性问题
- `_attempt_cycle_correction(cycles)`: 尝试自动修正循环依赖问题
- `_attempt_module_correction(module, issues)`: 尝试自动修正模块问题
- `_attempt_layer_correction(layer_name, issues)`: 尝试自动修正层级设计
- `_apply_correction(correction)`: 应用架构修正

**LLM 交互方法：**
- `_get_llm_response(prompt)`: 获取 LLM 响应
- `_generate_pattern_docs(pattern)`: 为特定架构模式生成详细文档
- `_generate_pattern_overview(pattern)`: 生成架构模式概述
- `_generate_layers_design(pattern)`: 生成层级设计文档
- `_generate_interface_definitions(pattern)`: 生成接口定义文档
- `_generate_dependency_specs(pattern)`: 生成依赖关系文档
- `_generate_module_spec(module, layer_info)`: 生成模块规范
- `_generate_consistency_correction_plan(issues)`: 生成架构一致性问题的修正方案
- `_generate_cycle_correction_plan(cycles)`: 生成循环依赖的修正方案

**架构验证方法：**
- `_validate_layer_design(layer_name, layer_info, related_components)`: 验证层级设计的合理性
- `_validate_with_relationships(layer_name, layer_info, related_components)`: 使用相关性信息验证设计
- `_validate_responsibilities(responsibilities)`: 验证职责定义的完整性
- `_validate_components(components)`: 验证组件设计的合理性
- `_validate_dependencies(dependencies)`: 验证依赖关系的合理性

**其他辅助方法：**
- `_find_related_components(pattern)`: 使用架构索引查找相关组件
- `_extract_pattern_keywords(pattern)`: 从模式描述中提取关键字
- `_check_feature_overlaps(layer_info, related_features)`: 检查功能重叠
- `_check_domain_consistency(layer_info, related_domains)`: 检查领域一致性
- `_check_dependency_rationality(layer_info, related_deps)`: 检查依赖合理性
- `_process_layer_modules(layer_name, layer_info)`: 处理层级中的模块
- `_handle_validation_issues(issues, module)`: 处理验证问题
- `_handle_layer_issues(layer_name, issues)`: 处理层级设计中发现的问题
- `_validate_overall_architecture()`: 执行整体架构验证
- `_save_final_architecture()`: 保存最终的架构状态

## 依赖关系
- `ArchitectureManager`: 用于管理架构索引和状态
- `llm_executor.run_prompt`: 用于执行 LLM 提示并获取响应
- 标准库: typing, pathlib, json, asyncio, re, datetime

## 文件操作
- 读取和写入 JSON 文件
- 创建架构文档 (.md 文件)
- 保存架构状态

## 错误处理
- 使用 try/except 处理 LLM 调用错误
- 使用日志记录器记录错误和警告
- 提供默认值和回退机制

## 测试策略

### 单元测试
1. **初始化测试**
   - 测试默认初始化
   - 测试提供自定义参数初始化

2. **LLM 交互测试**
   - 测试 _get_llm_response 方法
   - 模拟 LLM 响应
   - 测试错误处理

3. **架构问题检测测试**
   - 测试 _check_naming_inconsistencies 方法
   - 测试 _check_layer_violations 方法
   - 测试 _check_responsibility_overlaps 方法
   - 测试 _check_global_circular_dependencies 方法
   - 测试 _check_overall_consistency 方法

4. **架构验证测试**
   - 测试 _validate_layer_design 方法
   - 测试 _validate_with_relationships 方法
   - 测试 _validate_responsibilities 方法
   - 测试 _validate_components 方法
   - 测试 _validate_dependencies 方法

5. **公共方法测试**
   - 测试 check_all_issues 方法
   - 测试 check_module_issues 方法
   - 测试 start_deep_reasoning 方法

### 集成测试
1. **与 ArchitectureManager 集成测试**
   - 测试 populate_architecture_index 方法
   - 测试 _process_layer_modules 方法
   - 测试 _save_final_architecture 方法

2. **与 LLM 集成测试**
   - 测试文档生成方法
   - 测试修正方案生成方法

3. **端到端测试**
   - 测试完整的深度推理流程
   - 测试问题检测和修正流程

### 模拟依赖
- 使用 unittest.mock 模拟 ArchitectureManager
- 使用 unittest.mock 模拟 LLM 响应
- 使用临时目录进行文件操作测试

### 测试边缘情况
- 空输入
- 错误输入
- LLM 调用失败
- 文件操作失败
