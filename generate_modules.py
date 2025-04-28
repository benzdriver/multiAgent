"""
Generate modules from technical-architecture.md file
"""
import asyncio
import json
import os
from pathlib import Path
from core.clarifier.clarifier import Clarifier
from core.llm.chat_openai import chat as openai_chat

async def generate_modules():
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
    
    print("🔄 Generating modules from technical documentation...")
    
    module_categories = [
        "Frontend", "Backend", "Authentication", "Profile", "Assessment", 
        "Documents", "Forms", "Consultants", "Workspace", "Dashboard"
    ]
    
    output_dir = Path("data/output/modules")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for category in module_categories:
        print(f"🔄 Generating modules for {category}...")
        
        prompt = f"""
        Based on the following technical architecture documentation, generate a module for the {category} category.
        Extract the relevant information from the documentation and create a structured module summary.
        
        Technical Documentation:
        {content[:10000]}  # Limit content length to avoid token limits
        
        Return a JSON object with the following structure:
        {{
            "module_name": "string",
            "responsibilities": ["string"],
            "layer": "string",
            "domain": "string",
            "dependencies": ["string"],
            "requirements": ["string"],
            "target_path": "string"
        }}
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
                            print(f"✅ Successfully extracted JSON from markdown")
                        except json.JSONDecodeError as je:
                            print(f"❌ Failed to parse extracted JSON: {je}")
                else:
                    try:
                        result = json.loads(result)
                        print(f"✅ Successfully parsed string as JSON")
                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse response as JSON")
            
            if isinstance(result, dict) and "module_name" in result:
                module_name = result["module_name"]
                module_dir = output_dir / module_name
                module_dir.mkdir(parents=True, exist_ok=True)
                
                with open(module_dir / "full_summary.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Generated module: {module_name}")
            else:
                print(f"❌ Failed to generate module for {category}: {result}")
        except Exception as e:
            print(f"❌ Error generating module for {category}: {str(e)}")
    
    print("🔄 Integrating generated modules...")
    integration_result = await clarifier.integrate_legacy_modules()
    print(f"✅ Integrated {integration_result.get('modules_count', 0)} modules")
    
    if integration_result.get('circular_dependencies'):
        print(f"⚠️ Detected {len(integration_result['circular_dependencies'])} circular dependencies")
    else:
        print("✅ No circular dependencies detected")
    
    print("✅ Module generation complete!")

if __name__ == "__main__":
    asyncio.run(generate_modules())
