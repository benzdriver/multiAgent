# architecture_manager.py 模块分析

## 模块概述
architecture_manager.py 模块是 core/clarifier 包中的核心组件，负责管理架构索引、验证新模块，以及协调整体架构状态。该模块包含三个主要类：ArchitectureIndex、ArchitectureValidator 和 ArchitectureManager。

## 类和方法

### 1. ArchitectureIndex
管理各种架构索引，包括需求-模块映射、职责索引、依赖图和层级索引。

**主要方法：**
- `__init__()`: 初始化索引和预定义架构模式
- `add_module(module, requirements)`: 添加新模块到索引
- `_extract_keywords(text)`: 从文本中提取关键字
- `get_allowed_dependencies(pattern, layer)`: 获取特定架构模式和层级允许的依赖
- `get_layer_path(pattern, layer)`: 获取特定架构模式和层级的文件路径

**主要属性：**
- `requirement_module_index`: 需求到模块的映射
- `responsibility_index`: 职责索引
- `dependency_graph`: 依赖图
- `layer_index`: 层级索引
- `architecture_patterns`: 预定义架构模式

### 2. ArchitectureValidator
验证新模块的合理性，检查职责重叠、循环依赖和层级违规。

**主要方法：**
- `__init__(index)`: 初始化验证器
- `validate_new_module(module, requirements)`: 验证新模块的合理性
- `get_validation_issues()`: 获取所有验证问题
- `_check_responsibility_overlaps(module)`: 检查职责重叠
- `_check_circular_dependencies(module)`: 检查循环依赖
- `_check_layer_violations(module)`: 检查层级违规

**主要属性：**
- `index`: ArchitectureIndex 实例
- `validation_issues`: 验证问题字典

### 3. ArchitectureManager
协调索引和验证器，处理新模块，管理架构状态。

**主要方法：**
- `__init__()`: 初始化管理器
- `get_validation_issues()`: 获取所有架构验证问题
- `add_module(module_data)`: 添加或更新模块
- `add_requirement(req_data)`: 添加或更新需求
- `process_new_module(module_spec, requirements)`: 处理新模块
- `_save_architecture_state()`: 保存当前架构状态

**主要属性：**
- `index`: ArchitectureIndex 实例
- `validator`: ArchitectureValidator 实例
- `output_path`: 输出路径
- `modules`: 模块列表
- `requirements`: 需求列表

## 文件操作
- 读取和写入 JSON 文件
- 创建模块目录
- 保存架构状态到 data/output/architecture/architecture_state.json
- 创建模块摘要文件 full_summary.json

## 错误处理
- 处理 JSON 解析错误
- 处理文件操作异常
- 验证失败时返回错误信息

## 依赖和交互
- ArchitectureManager 被 clarifier.py 和 architecture_reasoner.py 导入和使用
- ArchitectureValidator 依赖 ArchitectureIndex 进行验证
- ArchitectureManager 协调 ArchitectureIndex 和 ArchitectureValidator

## 测试策略

### 单元测试
1. **ArchitectureIndex 测试**
   - 测试初始化是否正确设置属性
   - 测试添加模块到索引
   - 测试提取关键字
   - 测试获取允许的依赖
   - 测试获取层级路径

2. **ArchitectureValidator 测试**
   - 测试初始化是否正确设置属性
   - 测试验证新模块
   - 测试获取验证问题
   - 测试检查职责重叠
   - 测试检查循环依赖
   - 测试检查层级违规

3. **ArchitectureManager 测试**
   - 测试初始化是否正确设置属性
   - 测试获取验证问题
   - 测试添加或更新模块
   - 测试添加或更新需求
   - 测试处理新模块
   - 测试保存架构状态

### 集成测试
1. **ArchitectureManager 与 ArchitectureValidator 集成**
   - 测试验证新模块并处理验证结果
   - 测试验证失败时的行为

2. **ArchitectureManager 与文件系统集成**
   - 测试创建模块目录和摘要文件
   - 测试保存架构状态

3. **ArchitectureManager 与其他模块集成**
   - 测试与 clarifier.py 的集成
   - 测试与 architecture_reasoner.py 的集成

### 模拟依赖
- 使用 unittest.mock 模拟文件操作
- 使用临时目录进行文件操作测试
- 模拟 JSON 解析错误

### 测试边缘情况
- 空输入
- 错误输入
- 循环依赖
- 职责重叠
- 层级违规
