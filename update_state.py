"""
Update WebUI global state with modules from data/output/modules
"""
import asyncio
import json
import os
from pathlib import Path
import requests

async def update_state():
    print("🔄 Loading modules from data/output/modules...")
    
    modules_dir = Path("data/output/modules")
    if not modules_dir.exists():
        print(f"❌ Directory not found: {modules_dir}")
        return
    
    data = {
        "modules": {},
        "requirements": {},
        "requirement_module_index": {}
    }
    
    module_count = 0
    for module_dir in modules_dir.iterdir():
        if not module_dir.is_dir():
            continue
            
        summary_path = module_dir / "full_summary.json"
        if not summary_path.exists():
            print(f"⚠️ No full_summary.json found in {module_dir}")
            continue
            
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                module_data = json.load(f)
                
            module_name = module_data.get("module_name", "unknown")
            module_id = module_name.replace(" ", "_").lower()
            
            if "name" not in module_data:
                module_data["name"] = module_name
                
            data["modules"][module_id] = module_data
            
            for i, req in enumerate(module_data.get("requirements", [])):
                req_id = f"req_{i+1}"
                if req_id not in data["requirements"]:
                    data["requirements"][req_id] = {
                        "id": req_id,
                        "name": req,
                        "description": req,
                        "priority": "medium"
                    }
                
                if req_id not in data["requirement_module_index"]:
                    data["requirement_module_index"][req_id] = []
                    
                if module_id not in data["requirement_module_index"][req_id]:
                    data["requirement_module_index"][req_id].append(module_id)
            
            module_count += 1
            print(f"✅ Loaded module: {module_name}")
        except Exception as e:
            print(f"❌ Error loading module {module_dir.name}: {str(e)}")
    
    print(f"✅ Loaded {module_count} modules")
    
    with open("data/output/loaded_modules.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved loaded data to data/output/loaded_modules.json")
    
    try:
        print("🔄 Trying to update global state via chat API...")
        message = {
            "content": json.dumps(data)
        }
        response = requests.post("http://localhost:8080/api/chat", json=message)
        if response.status_code == 200:
            print(f"✅ Successfully sent data via chat API: {response.json()}")
        else:
            print(f"❌ Failed to send data via chat API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error sending data via chat API: {str(e)}")
    
    try:
        print("🔄 Trying to update requirements...")
        for req_id, req_data in data["requirements"].items():
            response = requests.post(f"http://localhost:8080/api/requirement/{req_id}", json=req_data)
            if response.status_code == 200:
                print(f"✅ Successfully updated requirement {req_id}: {response.json()}")
            else:
                print(f"❌ Failed to update requirement {req_id}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error updating requirements: {str(e)}")
    
    try:
        print("🔄 Checking dependencies...")
        response = requests.get("http://localhost:8080/api/check_dependencies")
        if response.status_code == 200:
            print(f"✅ Dependencies check result: {response.json()}")
        else:
            print(f"❌ Failed to check dependencies: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error checking dependencies: {str(e)}")

if __name__ == "__main__":
    asyncio.run(update_state())
