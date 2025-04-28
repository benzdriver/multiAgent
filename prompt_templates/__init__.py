"""
统一的prompt模板库初始化文件
"""

from prompt_templates.architecture_conventions import (
    get_architecture_conventions,
    infer_module_layer,
    get_clarifier_prompt,
    get_validator_prompt,
    get_fixer_prompt,
    get_generator_prompt,
    get_missing_module_summary_prompt
) 