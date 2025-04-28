"""
统一prompt模板库的使用示例

此示例展示了如何在不同组件中使用统一的prompt模板。
"""

import json
from pathlib import Path
from prompt_templates import (
    get_architecture_conventions,
    infer_module_layer,
    get_clarifier_prompt,
    get_validator_prompt,
    get_fixer_prompt,
    get_generator_prompt,
    get_missing_module_summary_prompt
)

def example_clarifier():
    """展示如何在clarifier中使用统一模板"""
    print("===== Clarifier Prompt 示例 =====")
    prompt = get_clarifier_prompt(1, 5)  # 第1部分，共5部分
    print(prompt[:300] + "...\n")  # 打印前300个字符

def example_validator():
    """展示如何在validator中使用统一模板"""
    print("===== Validator Prompt 示例 =====")
    # 模拟边界分析数据
    boundary_analysis = {
        "merge_suggestions": [
            {"modules": ["UserController", "ProfileController"], "reason": "命名相似且职责重叠"}
        ],
        "split_suggestions": [
            {"module": "AuthService", "reason": "职责过多 (10 个职责)"}
        ]
    }
    prompt = get_validator_prompt(2, 5, boundary_analysis)  # 第2部分，共5部分，带边界分析
    print(prompt[:300] + "...\n")  # 打印前300个字符

def example_fixer():
    """展示如何在fixer中使用统一模板"""
    print("===== Fixer Prompt 示例 =====")
    # 模拟模块摘要和问题
    original_summary = {
        "module_name": "UserController",
        "responsibilities": ["处理用户相关HTTP请求"],
        "key_apis": ["getAllUsers", "getUser"],  # 注意：这不是HTTP路径格式，是问题
        "data_inputs": ["userId"],
        "data_outputs": ["User对象"],
        "depends_on": ["UserRepository"],  # 注意：控制器直接依赖仓库，是问题
        "target_path": "backend/controllers"
    }
    issues = "1. key_apis 应该使用HTTP路径格式 (如 'GET /api/users')\n2. 控制器直接依赖仓库，应该依赖服务层"
    
    prompt = get_fixer_prompt("UserController", issues, original_summary)
    print(prompt[:300] + "...\n")  # 打印前300个字符

def example_generator():
    """展示如何在generator中使用统一模板"""
    print("===== Generator Prompt 示例 =====")
    # 模拟模块摘要
    module_summary = {
        "module_name": "UserService",
        "responsibilities": ["管理用户数据", "处理用户业务逻辑"],
        "key_apis": ["getUserById(id)", "createUser(userData)", "updateUser(id, userData)"],
        "data_inputs": ["用户ID", "用户数据"],
        "data_outputs": ["User对象"],
        "depends_on": ["UserRepository"],
        "target_path": "backend/services"
    }
    
    prompt = get_generator_prompt(module_summary)
    print(prompt[:300] + "...\n")  # 打印前300个字符

def example_missing_module():
    """展示如何生成缺失模块的摘要提示"""
    print("===== 缺失模块摘要 Prompt 示例 =====")
    prompt = get_missing_module_summary_prompt("UserRepository")
    print(prompt[:300] + "...\n")  # 打印前300个字符

def example_layer_inference():
    """展示如何根据模块名推断层级"""
    print("===== 层级推断示例 =====")
    modules = [
        "UserController", 
        "AuthService", 
        "ProductRepository", 
        "OrderModel", 
        "EmailClient",
        "GenericModule"  # 无明确后缀
    ]
    
    for module in modules:
        layer_info = infer_module_layer(module)
        print(f"{module}: {layer_info['layer']} 层, API格式: {layer_info['expected_api_format']}, 路径: {layer_info['target_path']}")

if __name__ == "__main__":
    # 打印架构约定
    print("===== 架构约定 =====")
    conventions = get_architecture_conventions()
    print(conventions[:300] + "...\n")  # 打印前300个字符
    
    # 展示各组件的使用示例
    example_clarifier()
    example_validator()
    example_fixer()
    example_generator()
    example_missing_module()
    example_layer_inference() 