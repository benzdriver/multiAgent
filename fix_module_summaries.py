"""
修复模块摘要文件脚本

此脚本用于检查和修复data/output/modules目录中的模块摘要文件，
确保每个模块都有完整的full_summary.json文件。
"""

import os
import json
import traceback
from pathlib import Path
import shutil
import re

def sanitize_module_name(name):
    """创建安全的模块名称（移除特殊字符）"""
    safe_name = name.replace(' ', '_')
    safe_name = re.sub(r'[^\w\-]', '', safe_name)
    return safe_name

def ensure_module_summary(module_dir, module_name):
    """确保模块目录中存在full_summary.json文件"""
    summary_file = module_dir / "full_summary.json"
    
    if not summary_file.exists():
        print(f"⚠️ 模块 '{module_name}' 缺少摘要文件，创建默认摘要")
        
        json_files = list(module_dir.glob("*.json"))
        if json_files:
            print(f"✅ 找到替代JSON文件: {json_files[0].name}")
            try:
                with open(json_files[0], "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if "name" not in data:
                    data["name"] = module_name
                if "description" not in data:
                    data["description"] = f"{module_name}模块"
                if "responsibilities" not in data:
                    data["responsibilities"] = [f"负责{module_name}相关功能"]
                if "dependencies" not in data:
                    data["dependencies"] = []
                if "layer" not in data:
                    data["layer"] = "未指定"
                if "domain" not in data:
                    data["domain"] = "未指定"
                
                with open(summary_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ 已从替代文件创建摘要: {summary_file}")
                return True
            except Exception as e:
                print(f"❌ 处理替代JSON文件时出错: {str(e)}")
        
        default_summary = {
            "name": module_name,
            "description": f"{module_name}模块",
            "responsibilities": [f"负责{module_name}相关功能"],
            "dependencies": [],
            "layer": "未指定",
            "domain": "未指定"
        }
        
        try:
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(default_summary, f, ensure_ascii=False, indent=2)
            print(f"✅ 已创建默认摘要: {summary_file}")
            return True
        except Exception as e:
            print(f"❌ 创建默认摘要失败: {str(e)}")
            return False
    else:
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            missing_fields = []
            for field in ["name", "description", "responsibilities", "dependencies", "layer", "domain"]:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️ 模块 '{module_name}' 摘要缺少字段: {', '.join(missing_fields)}")
                
                for field in missing_fields:
                    if field == "name":
                        data["name"] = module_name
                    elif field == "description":
                        data["description"] = f"{module_name}模块"
                    elif field == "responsibilities":
                        data["responsibilities"] = [f"负责{module_name}相关功能"]
                    elif field == "dependencies":
                        data["dependencies"] = []
                    elif field == "layer":
                        data["layer"] = "未指定"
                    elif field == "domain":
                        data["domain"] = "未指定"
                
                with open(summary_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ 已修复摘要文件中的缺失字段: {summary_file}")
            else:
                print(f"✓ 模块 '{module_name}' 摘要文件完整")
            
            return True
        except Exception as e:
            print(f"❌ 验证摘要文件失败: {str(e)}")
            return False

def create_safe_module_directories():
    """为所有模块创建安全名称的目录和摘要文件"""
    modules_dir = Path("data/output/modules")
    if not modules_dir.exists():
        print(f"❌ 模块目录不存在: {modules_dir}")
        return
    
    module_dirs = [d for d in modules_dir.iterdir() if d.is_dir()]
    print(f"找到 {len(module_dirs)} 个模块目录")
    
    for module_dir in module_dirs:
        module_name = module_dir.name
        print(f"\n处理模块: {module_name}")
        
        ensure_module_summary(module_dir, module_name)
        
        safe_name = sanitize_module_name(module_name)
        if safe_name != module_name:
            safe_dir = modules_dir / safe_name
            
            if not safe_dir.exists():
                try:
                    safe_dir.mkdir(parents=True, exist_ok=True)
                    print(f"✅ 创建安全名称目录: {safe_dir}")
                    
                    summary_file = module_dir / "full_summary.json"
                    if summary_file.exists():
                        safe_summary_file = safe_dir / "full_summary.json"
                        
                        with open(summary_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        data["safe_module_name"] = safe_name
                        
                        with open(safe_summary_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        
                        print(f"✅ 创建安全名称摘要文件: {safe_summary_file}")
                except Exception as e:
                    print(f"❌ 创建安全名称目录失败: {str(e)}")
                    traceback.print_exc()

def main():
    """主函数"""
    print("开始修复模块摘要文件...")
    
    try:
        os.makedirs("data/output/modules", exist_ok=True)
        
        create_safe_module_directories()
        
        print("\n✅ 模块摘要修复完成")
    except Exception as e:
        print(f"❌ 修复过程中出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
