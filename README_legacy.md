# 🧠 Multi-Agent AI Architecture Generator

This project automates the process of:
- Analyzing architecture and requirement documents
- Extracting functional modules
- Generating full-stack code for each module using LLMs
- Validating coverage and consistency

## 🧩 Project Structure

```
clarifier/            # Extracts modules from docs, builds summaries
├── clarifier.py
├── summarizer.py
├── index_generator.py
├── validator.py
├── structure_validator.py
├── vector_builder.py

memory/               # Manages vector DB + structured context
├── embedding_client.py
├── structured_context.py
├── function_signatures.py

llm/                  # Unified interface to chat models
├── chat_openai.py
├── chat_autogen.py
├── llm_executor.py
├── prompt_cleaner.py

generator/            # Generates real code from modules
├── autogen_module_generator.py

data/
├── input/            # Markdown documents (technical-architecture.md, requirement.md)
├── output/           # Output summaries & indexes
├── generated_code/   # Final generated code files
├── vector/           # Vector DB for memory

run_clarifier.py      # Step 1: Extract modules from docs
run_generator.py      # Step 2: Generate code from summaries
run_validator.py      # Step 3: Validate completeness & structure
run_fix.py            # Step 4: Automatically fix missing modules
```

---

## 🚀 How to Use

### 1. Drop Your Documents
Put your files into:
```
data/input/technical-architecture.md
data/input/requirement-md.md
```

### 2. Build Vector Memory
```bash
python -m clarifier.vector_builder
```

### 3. Clarify Modules from Documents
```bash
python run_clarifier.py
```
- Generates `full_summary.json` for each module
- Builds `summary_index.json`

### 4. Generate Code for All Modules
```bash
python run_generator.py --all
```
Or only specific modules:
```bash
python run_generator.py --only AuthService BookingPage
```

### 5. Validate Architecture Coverage
```bash
python run_validator.py
```
- Generates `validator_report.md`
- Checks for missing, redundant, overlapping, or undefined modules

### 6. Auto-Fix Missing Modules
```bash
python run_fix.py
```
- Parses `validator_report.md`
- Auto-generates missing summaries with LLM

---

## 🧠 Memory Strategy
This system uses:
- 🔍 Full-document chunking → local embedding search
- 🧠 `structured_context.py` to assemble:
  - responsibilities
  - dependencies
  - function signatures
  - semantic memory excerpts

---

## ✅ Status
- [x] Clarifier: Multi-chunk + JSON extraction
- [x] Generator: Full structured prompt + LLM continuation
- [x] Validator: Dual strategy (LLM + static analysis)
- [x] Fixer: Auto-regen summaries for missing modules
- [x] Vector memory pluggable (local now, 3rd party later)


## 🧩 TODO
- [ ] UI for summary/code browsing
- [ ] Code quality scoring and lint fixes
- [ ] Agent-based multi-round refinement

# Prompt Templates 统一模板库

这是一个为多代理AI系统设计的统一prompt模板库，旨在提供一致的架构约定和命名规范，确保在不同的系统组件之间保持一致性。

## 目的

- 统一架构约定和命名规范
- 确保API格式符合各层要求
- 自动根据模块名推断架构层级
- 提供标准化的prompt模板给各个组件使用

## 架构约定

系统遵循明确的分层架构，每层有特定的命名规范和API格式：

1. **表示层** (Controller, Page, View)：处理HTTP请求/响应，使用HTTP路径格式API
2. **业务逻辑层** (Service)：实现业务逻辑，使用方法名格式API
3. **数据访问层** (Repository, DAO)：数据库交互，使用数据操作方法格式API
4. **模型层** (Model, Entity, Schema)：定义数据结构，使用属性和方法格式API
5. **工具层** (Util, Helper, Client)：提供通用功能，使用工具方法格式API

## 提供的功能

- `get_architecture_conventions()`: 返回系统架构约定的标准描述
- `infer_module_layer(module_name)`: 根据模块名称推断其架构层级
- `get_clarifier_prompt(part_num, total_parts)`: 返回用于Clarifier的模块识别提示模板
- `get_validator_prompt(part_num, total_parts, boundary_analysis)`: 返回用于Validator的架构验证提示模板
- `get_fixer_prompt(module_name, issues, original_summary, related_modules)`: 返回用于Fixer的模块修复提示模板
- `get_generator_prompt(module_summary)`: 返回用于Generator的代码生成提示模板
- `get_missing_module_summary_prompt(module_name)`: 返回用于生成缺失模块摘要的提示模板

## 使用示例

```python
from prompt_templates import (
    get_architecture_conventions,
    infer_module_layer,
    get_clarifier_prompt,
    get_validator_prompt,
    get_fixer_prompt,
    get_generator_prompt,
    get_missing_module_summary_prompt
)

# 获取架构约定
conventions = get_architecture_conventions()

# 根据模块名推断层级
user_controller_info = infer_module_layer("UserController")
# 返回: {"layer": "presentation", "expected_api_format": "HTTP paths", ...}

# 在Clarifier中使用
clarifier_prompt = get_clarifier_prompt(1, 5)  # 第1部分，共5部分

# 在Validator中使用
validator_prompt = get_validator_prompt(2, 5, boundary_analysis)

# 在Fixer中使用
fixer_prompt = get_fixer_prompt("UserController", issues, original_summary)

# 在Generator中使用
generator_prompt = get_generator_prompt(module_summary)

# 生成缺失模块的摘要提示
missing_module_prompt = get_missing_module_summary_prompt("UserRepository")
```

更多详细示例，请参见 `prompt_templates/examples/usage_example.py`。

## 配置

模板库使用 `prompt_templates/config.json` 存储架构约定配置。首次导入时会自动创建此文件，也可以手动定制。
