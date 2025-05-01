# index_generator.py 模块分析

## 模块概述
index_generator.py 是 core/clarifier 包中的组件，负责生成架构模块的多维度索引。该模块读取模块摘要文件，生成不同类型的索引，并将索引保存为 JSON 文件。

## 类和方法

### MultiDimensionalIndexGenerator
主要类，提供多维度索引生成功能。

**初始化方法：**
- `__init__(modules_dir: Path, output_dir: Path)`: 初始化索引生成器，设置模块目录和输出目录。

**主要方法：**
- `load_modules() -> List[Dict]`: 加载所有模块的 full_summary.json 文件
- `generate_indices() -> Dict`: 生成多维度索引，协调所有索引生成过程

**私有方法：**
- `_generate_layer_index(modules: List[Dict]) -> None`: 生成层级索引
- `_generate_domain_index(modules: List[Dict]) -> None`: 生成领域索引
- `_generate_responsibility_index(modules: List[Dict]) -> None`: 生成职责索引
- `_generate_requirement_module_index(modules: List[Dict]) -> None`: 生成需求-模块索引
- `_generate_cross_cutting_index(modules: List[Dict]) -> None`: 生成横切关注点索引
- `_save_indices() -> None`: 保存所有生成的索引

## 依赖关系
- `Dict`, `List`, `Any` 从 typing 模块：用于类型注解
- `Path` 从 pathlib 模块：用于文件路径操作
- `json`：用于 JSON 序列化和反序列化
- `os`：用于文件系统操作

## 工作流程
1. 初始化索引生成器，设置模块目录和输出目录
2. 加载所有模块的 full_summary.json 文件
3. 生成各种类型的索引
   - 层级索引：基于模块所属层级
   - 领域索引：基于模块所属领域
   - 职责索引：基于模块职责
   - 需求-模块索引：基于模块相关需求
   - 横切关注点索引：基于模块涉及的横切关注点
4. 保存所有生成的索引到 JSON 文件

## 文件操作
- 读取模块目录中的 full_summary.json 文件
- 创建输出目录
- 保存索引到 JSON 文件

## 错误处理
- 使用 try/except 处理文件读取错误
- 使用 try/except 处理文件写入错误
- 打印错误信息到控制台

## 索引结构
- 层级索引：支持层级嵌套（使用点号分隔）
- 领域索引：将模块按领域分组
- 职责索引：将模块按职责分组
- 需求-模块索引：将模块按相关需求分组
- 横切关注点索引：将模块按横切关注点分组

## 测试策略

### 单元测试
1. **初始化测试**
   - 测试默认初始化
   - 测试目录创建

2. **模块加载测试**
   - 测试 load_modules 方法
   - 测试空目录情况
   - 测试无效 JSON 文件情况
   - 测试有效模块加载

3. **索引生成测试**
   - 测试 generate_indices 方法
   - 测试各个索引生成方法
   - 测试层级嵌套索引生成
   - 测试横切关注点检测

4. **索引保存测试**
   - 测试 _save_indices 方法
   - 测试文件写入错误处理

### 集成测试
1. **与文件系统集成测试**
   - 测试读取实际模块文件
   - 测试写入实际索引文件

2. **与其他模块集成测试**
   - 测试与 architecture_manager.py 的集成
   - 测试与 clarifier.py 的集成

3. **端到端测试**
   - 测试完整的索引生成流程
   - 测试从模块加载到索引保存的完整流程

### 模拟依赖
- 使用 unittest.mock 模拟文件操作
- 使用临时目录进行文件操作测试

### 测试边缘情况
- 空输入
- 错误输入
- 文件操作失败
- 特殊字符处理
- 层级嵌套过深
