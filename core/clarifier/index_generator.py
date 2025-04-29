from typing import Dict, List, Any
from pathlib import Path
import json
import os

class MultiDimensionalIndexGenerator:
    def __init__(self, modules_dir: Path, output_dir: Path):
        self.modules_dir = modules_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.dimensions = {
            "layer_index": {},       # 层级索引
            "domain_index": {},      # 领域索引
            "responsibility_index": {},  # 职责索引
            "requirement_module_index": {},  # 需求-模块索引
            "cross_cutting_index": {}    # 横切关注点索引
        }
        
    def load_modules(self) -> List[Dict]:
        """加载所有模块的full_summary.json"""
        modules = []
        
        for module_dir in self.modules_dir.iterdir():
            if not module_dir.is_dir():
                continue
                
            summary_path = module_dir / "full_summary.json"
            if not summary_path.exists():
                continue
                
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    module_data = json.load(f)
                    modules.append(module_data)
            except Exception as e:
                print(f"❌ 读取模块 {module_dir.name} 时出错: {str(e)}")
                
        return modules
        
    def generate_indices(self) -> Dict:
        """生成多维度索引"""
        modules = self.load_modules()
        print(f"📊 为 {len(modules)} 个模块生成多维度索引...")
        
        self._generate_layer_index(modules)
        
        self._generate_domain_index(modules)
        
        self._generate_responsibility_index(modules)
        
        self._generate_requirement_module_index(modules)
        
        self._generate_cross_cutting_index(modules)
        
        self._save_indices()
        
        return self.dimensions
        
    def _generate_layer_index(self, modules: List[Dict]) -> None:
        """生成层级索引"""
        for module in modules:
            layer = module.get("layer", "Unknown")
            if "." in layer:
                parts = layer.split(".")
                current = self.dimensions["layer_index"]
                
                for i, part in enumerate(parts):
                    if part not in current:
                        current[part] = {} if i < len(parts) - 1 else []
                    
                    if i == len(parts) - 1:
                        current[part].append(module.get("module_name"))
                    else:
                        current = current[part]
            else:
                if layer not in self.dimensions["layer_index"]:
                    self.dimensions["layer_index"][layer] = []
                self.dimensions["layer_index"][layer].append(module.get("module_name"))
      
    def _generate_domain_index(self, modules: List[Dict]) -> None:
        """生成领域索引"""
        for module in modules:
            domain = module.get("domain", "Unknown")
            if domain not in self.dimensions["domain_index"]:
                self.dimensions["domain_index"][domain] = []
            self.dimensions["domain_index"][domain].append(module.get("module_name"))
            
    def _generate_responsibility_index(self, modules: List[Dict]) -> None:
        """生成职责索引"""
        for module in modules:
            for resp in module.get("responsibilities", []):
                if resp not in self.dimensions["responsibility_index"]:
                    self.dimensions["responsibility_index"][resp] = []
                self.dimensions["responsibility_index"][resp].append(module.get("module_name"))
                
    def _generate_requirement_module_index(self, modules: List[Dict]) -> None:
        """生成需求-模块索引"""
        for module in modules:
            for req in module.get("requirements", []):
                if req not in self.dimensions["requirement_module_index"]:
                    self.dimensions["requirement_module_index"][req] = []
                self.dimensions["requirement_module_index"][req].append(module.get("module_name"))
                
    def _generate_cross_cutting_index(self, modules: List[Dict]) -> None:
        """生成横切关注点索引"""
        cross_cutting_concerns = [
            "Internationalization",
            "Authentication",
            "Logging",
            "Caching",
            "ErrorHandling",
            "Security",
            "Responsive"
        ]
        
        for concern in cross_cutting_concerns:
            self.dimensions["cross_cutting_index"][concern] = []
            
        for module in modules:
            for resp in module.get("responsibilities", []):
                for concern in cross_cutting_concerns:
                    if concern.lower() in resp.lower():
                        self.dimensions["cross_cutting_index"][concern].append(module.get("module_name"))
                        break
                        
            for dep in module.get("dependencies", []):
                for concern in cross_cutting_concerns:
                    if concern.lower() in dep.lower():
                        if module.get("module_name") not in self.dimensions["cross_cutting_index"][concern]:
                            self.dimensions["cross_cutting_index"][concern].append(module.get("module_name"))
                        break
                        
    def _save_indices(self) -> None:
        """保存所有索引"""
        indices_dir = self.output_dir / "indices"
        indices_dir.mkdir(parents=True, exist_ok=True)
        
        for name, data in self.dimensions.items():
            try:
                with open(indices_dir / f"{name}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存 {name} 到 {indices_dir / f'{name}.json'}")
            except Exception as e:
                print(f"❌ 保存 {name} 时出错: {str(e)}")
                
        try:
            with open(indices_dir / "all_indices.json", "w", encoding="utf-8") as f:
                json.dump(self.dimensions, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存合并索引到 {indices_dir / 'all_indices.json'}")
        except Exception as e:
            print(f"❌ 保存合并索引时出错: {str(e)}")
