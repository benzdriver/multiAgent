"""
Generate layered modules from technical-architecture.md file
This script creates more detailed modules reflecting the layered architecture:
- UI/View/Page components for frontend
- Model/Service/Controller/Repository components for backend

The script performs the following steps:
1. Extract functional and non-functional modules from technical documentation
2. Generate layer-specific modules for each domain
3. Create multi-dimensional indices for quick requirement-based lookup
4. Perform global validation checks (conflicts, circular dependencies, functional overlaps)
5. Prepare data for WebUI display
"""
import asyncio
import json
import os
from pathlib import Path
from core.clarifier.clarifier import Clarifier
from core.llm.chat_openai import chat as openai_chat

async def generate_layered_modules():
    clarifier = Clarifier(llm_chat=openai_chat)
    
    if not hasattr(clarifier, 'architecture_manager'):
        from core.clarifier.architecture_manager import ArchitectureManager
        clarifier.architecture_manager = ArchitectureManager()
        print("✅ Created architecture manager")
    
    input_path = Path("data/input/technical-architecture.md")
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        return
    
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"✅ Read {input_path.name} ({len(content)} characters)")
    
    layers = {
        "Presentation": [
            "UI Components", 
            "Pages", 
            "Views", 
            "Layout Components"
        ],
        "Business": [
            "Services", 
            "Controllers", 
            "Validators", 
            "Middleware"
        ],
        "Data": [
            "Models", 
            "Repositories", 
            "Data Access Objects", 
            "Data Transfer Objects"
        ],
        "Infrastructure": [
            "API Clients", 
            "Storage Services", 
            "Authentication Services", 
            "Logging Services"
        ]
    }
    
    functional_domains = [
        "Authentication", "Profile", "Assessment", "Documents", 
        "Forms", "Consultants", "Workspace", "Dashboard"
    ]
    
    non_functional_domains = [
        "Security", "Performance", "Scalability", "Reliability",
        "Maintainability", "Usability", "Accessibility"
    ]
    
    domains = functional_domains + non_functional_domains
    
    output_dir = Path("data/output/modules")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for item in output_dir.iterdir():
        if item.is_dir():
            for file in item.iterdir():
                file.unlink()
            item.rmdir()
    
    print("🔄 生成分层模块中...")
    print(f"📊 总计需要生成: {len(layers) * sum(len(components) for components in layers.values()) * len(domains)} 个模块")
    print(f"📋 层级: {list(layers.keys())}")
    print(f"📋 功能域: {functional_domains}")
    print(f"📋 非功能域: {non_functional_domains}")
    
    total_modules = len(layers) * sum(len(components) for components in layers.values()) * len(domains)
    generated_modules = 0
    skipped_modules = 0
    failed_modules = 0
    
    for layer, components in layers.items():
        print(f"\n🔄 生成 {layer} 层的模块...")
        for component in components:
            for domain in domains:
                generated_modules += 1
                print(f"🔄 [{generated_modules}/{total_modules}] 生成 {layer}/{component}/{domain} 模块...")
                
                layer_specific_guidance = {
                    "Presentation": "关注用户界面、交互体验和展示逻辑。依赖于Business层的服务，但不应直接访问Data层。",
                    "Business": "实现业务逻辑和规则，协调数据流。可以依赖Data层和Infrastructure层。",
                    "Data": "负责数据访问、持久化和数据转换。通常依赖Infrastructure层的服务。",
                    "Infrastructure": "提供技术基础设施和跨领域关注点。通常不依赖其他层。"
                }
                
                component_specific_guidance = {
                    "UI Components": "可重用的UI元素，如按钮、表单、卡片等。",
                    "Pages": "完整的页面组件，整合多个UI组件和视图。",
                    "Views": "特定功能区域的视图组件，可能包含多个UI组件。",
                    "Layout Components": "页面布局组件，如导航栏、侧边栏、页脚等。",
                    "Services": "实现业务逻辑的服务类，处理复杂业务规则。",
                    "Controllers": "处理请求和响应，协调服务和数据访问。",
                    "Validators": "验证输入数据的有效性和合法性。",
                    "Middleware": "请求处理管道中的中间件组件。",
                    "Models": "数据模型类，表示业务实体。",
                    "Repositories": "数据访问抽象，提供CRUD操作。",
                    "Data Access Objects": "直接与数据源交互的对象。",
                    "Data Transfer Objects": "在不同层之间传输数据的对象。",
                    "API Clients": "与外部API交互的客户端。",
                    "Storage Services": "提供存储服务的组件。",
                    "Authentication Services": "处理认证和授权的服务。",
                    "Logging Services": "提供日志记录功能的服务。"
                }
                
                prompt = f"""
                基于以下技术架构文档，为{layer}层的{component}组件在{domain}领域生成一个详细的模块。
                
                技术文档:
                {content[:15000]}
                
                层级指导: {layer_specific_guidance.get(layer, "")}
                组件指导: {component_specific_guidance.get(component, "")}
                
                请专注于创建一个准确反映文档中描述的分层架构的模块。
                对于这个特定组合({layer}/{component}/{domain})，请识别:
                1. 该模块应具有的具体职责
                2. 该模块对其他模块的依赖关系
                3. 该模块将满足的需求
                4. 该模块的适当目标路径
                
                返回一个具有以下结构的JSON对象:
                {{
                    "module_name": "{component} - {domain}",
                    "responsibilities": ["具体职责1", "具体职责2", ...],
                    "layer": "{layer}",
                    "domain": "{domain}",
                    "dependencies": ["依赖1", "依赖2", ...],
                    "requirements": ["需求1", "需求2", ...],
                    "target_path": "目标路径"
                }}
                
                请在分析中具体且详细。如果这个特定组合在架构中没有意义，请返回一个responsibilities、dependencies和requirements为空数组的JSON。
                
                注意：
                1. 确保职责与该层级和组件类型相符
                2. 依赖关系应遵循分层架构原则（例如，Presentation层不应直接依赖Data层）
                3. 需求应该是该模块将满足的具体功能或非功能需求
                4. 目标路径应反映模块在项目结构中的位置
                """
                
                try:
                    result = await clarifier.run_llm(prompt=prompt, return_json=True)
                    
                    if isinstance(result, str):
                        if "```json" in result:
                            json_start = result.find("```json") + 7
                            json_end = result.rfind("```")
                            if json_end > json_start:
                                json_str = result[json_start:json_end].strip()
                                try:
                                    result = json.loads(json_str)
                                    print(f"✅ 成功从Markdown中提取JSON")
                                except json.JSONDecodeError as je:
                                    print(f"❌ 解析提取的JSON失败: {je}")
                                    failed_modules += 1
                                    continue
                        else:
                            try:
                                result = json.loads(result)
                                print(f"✅ 成功将字符串解析为JSON")
                            except json.JSONDecodeError:
                                print(f"❌ 将响应解析为JSON失败")
                                failed_modules += 1
                                continue
                    
                    if isinstance(result, dict) and "module_name" in result:
                        if not result.get("responsibilities") or len(result.get("responsibilities", [])) == 0:
                            print(f"⚠️ 跳过 {result['module_name']} - 未识别到职责")
                            skipped_modules += 1
                            continue
                        
                        required_fields = ["module_name", "responsibilities", "layer", "domain", "dependencies", "requirements", "target_path"]
                        missing_fields = [field for field in required_fields if field not in result or result[field] is None]
                        
                        if missing_fields:
                            print(f"⚠️ 模块 {result.get('module_name', 'unknown')} 缺少必要字段: {', '.join(missing_fields)}")
                            for field in missing_fields:
                                if field in ["responsibilities", "dependencies", "requirements"]:
                                    result[field] = []
                                elif field == "target_path":
                                    result[field] = f"src/{domain.lower()}/{component.lower().replace(' ', '_')}"
                                else:
                                    result[field] = "unknown"
                        
                        module_name = result["module_name"]
                        module_dir = output_dir / module_name
                        module_dir.mkdir(parents=True, exist_ok=True)
                        
                        with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        
                        print(f"✅ 生成模块: {module_name}")
                    else:
                        print(f"❌ 为 {layer}/{component}/{domain} 生成模块失败: {result}")
                        failed_modules += 1
                except Exception as e:
                    print(f"❌ 为 {layer}/{component}/{domain} 生成模块时出错: {str(e)}")
                    failed_modules += 1
    
    print("🔄 集成生成的模块...")
    integration_result = await clarifier.integrate_legacy_modules()
    print(f"✅ 集成了 {integration_result.get('modules_count', 0)} 个模块")
    
    print("\n🔍 执行全局模块检查...")
    
    if integration_result.get('circular_dependencies'):
        print(f"⚠️ 检测到 {len(integration_result['circular_dependencies'])} 个循环依赖关系:")
        for cycle in integration_result['circular_dependencies']:
            print(f"  - {' -> '.join(cycle)}")
    else:
        print("✅ 未检测到循环依赖")
    
    try:
        layer_violations = await clarifier.check_layer_violations()
        if layer_violations:
            print(f"⚠️ 检测到 {len(layer_violations)} 个层级违规:")
            for violation in layer_violations:
                print(f"  - {violation['source']} -> {violation['target']}: {violation['message']}")
        else:
            print("✅ 未检测到层级违规")
    except Exception as e:
        print(f"❌ 检查层级违规时出错: {str(e)}")
    
    try:
        overlaps = await clarifier.check_responsibility_overlaps()
        if overlaps:
            print(f"⚠️ 检测到 {len(overlaps)} 个职能重叠:")
            for overlap in overlaps:
                print(f"  - {overlap['module1']} 和 {overlap['module2']}: {', '.join(overlap['responsibilities'][:3])}...")
        else:
            print("✅ 未检测到职能重叠")
    except Exception as e:
        print(f"❌ 检查职能重叠时出错: {str(e)}")
    
    print("🔄 Generating summary index...")
    summary_index = {
        "modules": {},
        "requirement_module_index": {},
        "responsibility_index": {},
        "layer_index": {},
        "domain_index": {}
    }
    
    for module_dir in output_dir.iterdir():
        if not module_dir.is_dir():
            continue
            
        summary_path = module_dir / "full_summary.json"
        if not summary_path.exists():
            continue
            
        with open(summary_path, "r", encoding="utf-8") as f:
            module_data = json.load(f)
            
        module_name = module_data.get("module_name", "unknown")
        module_id = module_name.replace(" ", "_").lower()
        
        summary_index["modules"][module_id] = module_data
        
        layer = module_data.get("layer", "unknown")
        if layer not in summary_index["layer_index"]:
            summary_index["layer_index"][layer] = []
        summary_index["layer_index"][layer].append(module_id)
        
        domain = module_data.get("domain", "unknown")
        if domain not in summary_index["domain_index"]:
            summary_index["domain_index"][domain] = []
        summary_index["domain_index"][domain].append(module_id)
        
        for resp in module_data.get("responsibilities", []):
            resp_key = resp[:50]  # Use first 50 chars as key
            if resp_key not in summary_index["responsibility_index"]:
                summary_index["responsibility_index"][resp_key] = []
            summary_index["responsibility_index"][resp_key].append(module_id)
        
        for i, req in enumerate(module_data.get("requirements", [])):
            req_id = f"req_{domain}_{i+1}"
            if req_id not in summary_index["requirement_module_index"]:
                summary_index["requirement_module_index"][req_id] = {
                    "name": req,
                    "modules": []
                }
            if module_id not in summary_index["requirement_module_index"][req_id]["modules"]:
                summary_index["requirement_module_index"][req_id]["modules"].append(module_id)
    
    with open("data/output/summary_index.json", "w", encoding="utf-8") as f:
        json.dump(summary_index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 生成摘要索引，包含 {len(summary_index['modules'])} 个模块")
    
    print("\n📊 模块生成统计报告:")
    print(f"  - 总计需要生成: {total_modules} 个模块")
    print(f"  - 成功生成: {len(summary_index['modules'])} 个模块")
    print(f"  - 跳过模块: {skipped_modules} 个")
    print(f"  - 生成失败: {failed_modules} 个")
    print(f"  - 成功率: {len(summary_index['modules']) / total_modules * 100:.2f}%")
    
    print("\n📊 按层级统计:")
    for layer, modules in summary_index["layer_index"].items():
        print(f"  - {layer}: {len(modules)} 个模块")
    
    print("\n📊 按领域统计:")
    for domain, modules in summary_index["domain_index"].items():
        print(f"  - {domain}: {len(modules)} 个模块")
    
    print("\n✅ 模块生成完成!")
    
    print("🔄 准备WebUI数据...")
    webui_data = {
        "modules": summary_index["modules"],
        "requirements": {},
        "requirement_module_index": {}
    }
    
    for req_id, req_data in summary_index["requirement_module_index"].items():
        webui_data["requirements"][req_id] = {
            "id": req_id,
            "name": req_data["name"],
            "description": req_data["name"],
            "priority": "medium"
        }
        webui_data["requirement_module_index"][req_id] = req_data["modules"]
    
    with open("data/output/loaded_modules.json", "w", encoding="utf-8") as f:
        json.dump(webui_data, f, ensure_ascii=False, indent=2)
    
    print("✅ WebUI数据准备完成")
    
    return webui_data

if __name__ == "__main__":
    asyncio.run(generate_layered_modules())
