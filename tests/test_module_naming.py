import unittest
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from prompt_templates.architecture_conventions import infer_module_layer, extract_domain_from_module_name

class TestModuleNaming(unittest.TestCase):
    def test_infer_module_layer(self):
        test_cases = [
            {
                "module_name": "UserController",
                "expected": {
                    "layer": "presentation",
                    "target_path": "frontend/controllers"
                }
            },
            {
                "module_name": "AuthService",
                "expected": {
                    "layer": "business",
                    "target_path": "backend/services"
                }
            },
            {
                "module_name": "UserRepository",
                "expected": {
                    "layer": "data_access",
                    "target_path": "backend/repositories"
                }
            },
            {
                "module_name": "UI_Components_-_Workspace",
                "expected": {
                    "layer": "presentation",
                    "target_path": "frontend/presentation/workspace"
                }
            },
            {
                "module_name": "Controllers - Authentication",
                "expected": {
                    "layer": "business",
                    "target_path": "backend/business/authentication"
                }
            }
        ]
        
        for case in test_cases:
            module_name = case["module_name"]
            result = infer_module_layer(module_name)
            print(f"Module: {module_name}, Result: {result}")
            self.assertEqual(result["layer"], case["expected"]["layer"])
            self.assertEqual(result["target_path"], case["expected"]["target_path"])
    
    def test_extract_domain_from_module_name(self):
        test_cases = [
            {"module_name": "UI_Components_-_Workspace", "expected": "workspace"},
            {"module_name": "Controllers - Authentication", "expected": "authentication"},
            {"module_name": "Layout_Components_-_Forms", "expected": "forms"},
            {"module_name": "Pages_-_Dashboard", "expected": "dashboard"},
            {"module_name": "Services_-_UserManagement", "expected": "usermanagement"}
        ]
        
        for case in test_cases:
            result = extract_domain_from_module_name(case["module_name"])
            self.assertEqual(result, case["expected"])

if __name__ == "__main__":
    unittest.main()
