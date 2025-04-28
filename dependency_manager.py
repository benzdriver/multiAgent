import json
from pathlib import Path
import re
import networkx as nx
import matplotlib.pyplot as plt

class DependencyManager:
    """管理模块依赖关系的类，提供实时更新和循环检测功能"""
    
    def __init__(self, graph_path="data/output/dependency_graph.json"):
        self.graph_path = Path(graph_path)
        self.graph = self._load_graph()
        self._ensure_nx_graph()
    
    def _load_graph(self):
        """加载或初始化依赖图"""
        if self.graph_path.exists():
            try:
                return json.loads(self.graph_path.read_text())
            except Exception as e:
                print(f"加载依赖图失败: {e}，创建新图")
        return {}
    
    def _ensure_nx_graph(self):
        """确保NetworkX图已创建并与当前依赖图同步"""
        self.digraph = nx.DiGraph()
        
        # 添加节点
        for module in self.graph:
            self.digraph.add_node(module)
        
        # 添加边
        for module, data in self.graph.items():
            for dep in data.get("depends_on", []):
                if dep in self.graph:  # 确保依赖存在
                    self.digraph.add_edge(module, dep)
    
    def save(self):
        """保存依赖图到文件"""
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.graph_path, 'w') as f:
            json.dump(self.graph, f, indent=2)
    
    def add_module(self, module_name, dependencies=None):
        """添加新模块到依赖图"""
        if dependencies is None:
            dependencies = []
        
        if module_name not in self.graph:
            self.graph[module_name] = {
                "depends_on": dependencies,
                "depended_by": []
            }
        else:
            # 更新现有模块的依赖
            self.graph[module_name]["depends_on"] = list(set(
                self.graph[module_name]["depends_on"] + dependencies
            ))
        
        # 更新被依赖关系
        for dep in dependencies:
            if dep in self.graph:
                if module_name not in self.graph[dep]["depended_by"]:
                    self.graph[dep]["depended_by"].append(module_name)
            else:
                # 如果依赖模块不存在，创建它
                self.graph[dep] = {
                    "depends_on": [],
                    "depended_by": [module_name]
                }
        
        # 更新NetworkX图
        self.digraph.add_node(module_name)
        for dep in dependencies:
            self.digraph.add_node(dep)
            self.digraph.add_edge(module_name, dep)
        
        self.save()
        
        # 检查是否引入了循环依赖
        return self.check_circular_dependencies(module_name)
    
    def remove_module(self, module_name):
        """从依赖图中移除模块"""
        if module_name in self.graph:
            # 移除被依赖关系
            for dep in self.graph[module_name]["depends_on"]:
                if dep in self.graph and module_name in self.graph[dep]["depended_by"]:
                    self.graph[dep]["depended_by"].remove(module_name)
            
            # 移除对此模块的依赖
            for mod, data in self.graph.items():
                if module_name in data["depends_on"]:
                    data["depends_on"].remove(module_name)
            
            # 删除模块
            del self.graph[module_name]
            
            # 更新NetworkX图
            if self.digraph.has_node(module_name):
                self.digraph.remove_node(module_name)
            
            self.save()
    
    def update_dependencies(self, module_name, new_dependencies):
        """更新模块的依赖，返回是否引入循环依赖"""
        if module_name not in self.graph:
            return self.add_module(module_name, new_dependencies)
        
        # 移除当前依赖关系
        old_dependencies = self.graph[module_name]["depends_on"]
        for dep in old_dependencies:
            if dep in self.graph and module_name in self.graph[dep]["depended_by"]:
                self.graph[dep]["depended_by"].remove(module_name)
                if self.digraph.has_edge(module_name, dep):
                    self.digraph.remove_edge(module_name, dep)
        
        # 添加新依赖关系
        self.graph[module_name]["depends_on"] = new_dependencies
        for dep in new_dependencies:
            if dep in self.graph:
                if module_name not in self.graph[dep]["depended_by"]:
                    self.graph[dep]["depended_by"].append(module_name)
            else:
                self.graph[dep] = {
                    "depends_on": [],
                    "depended_by": [module_name]
                }
            self.digraph.add_node(dep)
            self.digraph.add_edge(module_name, dep)
        
        self.save()
        
        # 检查是否引入了循环依赖
        return self.check_circular_dependencies(module_name)
    
    def check_circular_dependencies(self, start_module=None):
        """检查是否存在循环依赖，如果指定了起始模块，则只检查与该模块相关的循环"""
        try:
            if start_module:
                # 只检查与指定模块相关的循环
                descendants = set(nx.descendants(self.digraph, start_module))
                if descendants:
                    subgraph = self.digraph.subgraph(descendants.union({start_module}))
                    cycles = list(nx.simple_cycles(subgraph))
                else:
                    cycles = []
            else:
                # 检查所有循环
                cycles = list(nx.simple_cycles(self.digraph))
            
            return {
                "has_cycles": len(cycles) > 0,
                "cycles": cycles
            }
        except Exception as e:
            print(f"检查循环依赖时出错: {e}")
            return {"has_cycles": False, "cycles": []}
    
    def get_topological_order(self):
        """获取模块的拓扑排序（如果没有循环依赖）"""
        try:
            return list(nx.topological_sort(self.digraph))
        except nx.NetworkXUnfeasible:
            # 有循环依赖，无法进行拓扑排序
            return None
    
    def visualize(self, output_path="data/output/dependency_graph.png"):
        """将依赖图可视化并保存为图片"""
        plt.figure(figsize=(12, 10))
        pos = nx.spring_layout(self.digraph)
        nx.draw(
            self.digraph, pos, with_labels=True, 
            node_color='skyblue', node_size=1500, 
            arrows=True, arrowsize=15
        )
        plt.title("Module Dependency Graph")
        plt.savefig(output_path)
        print(f"依赖图已保存到 {output_path}")
        
    def build_from_modules(self, modules_dir="data/output/modules"):
        """从模块定义目录构建依赖图"""
        modules_dir = Path(modules_dir)
        self.graph = {}
        
        if not modules_dir.exists():
            print(f"模块目录不存在: {modules_dir}")
            return
            
        # 第一遍: 收集所有模块
        for module_dir in modules_dir.glob("*"):
            if module_dir.is_dir():
                summary_file = module_dir / "full_summary.json"
                if summary_file.exists():
                    try:
                        data = json.loads(summary_file.read_text())
                        module_name = data.get("module_name")
                        if module_name:
                            self.graph[module_name] = {
                                "depends_on": data.get("depends_on", []),
                                "depended_by": [],
                                "target_path": data.get("target_path", "")
                            }
                    except Exception as e:
                        print(f"处理模块 {module_dir.name} 时出错: {e}")
        
        # 第二遍: 填充 depended_by 字段
        for name, data in self.graph.items():
            for dep in data["depends_on"]:
                if dep in self.graph:
                    if name not in self.graph[dep]["depended_by"]:
                        self.graph[dep]["depended_by"].append(name)
        
        # 更新NetworkX图
        self._ensure_nx_graph()
        self.save()
        
        print(f"✅ 从 {len(self.graph)} 个模块构建了依赖图")
        return self.graph

# 使用示例
def initialize_dependency_graph():
    """初始化并返回依赖图管理器"""
    manager = DependencyManager()
    manager.build_from_modules()
    return manager 