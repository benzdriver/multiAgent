"""
Tests for the module validator functionality.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the architecture package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from architecture.module_validator import (
    is_valid_module_name,
    get_valid_module_path,
    validate_module_dependencies
)
from architecture.module_conventions import (
    infer_module_layer,
    get_all_architecture_layers,
    get_layer_by_name
)


class TestModuleValidator(unittest.TestCase):
    
    def test_valid_module_names(self):
        valid_modules = [
            "UserController",
            "ProductService",
            "CustomerRepository",
            "OrderModel",
            "LoggingUtil",
            "AuthHelper", 
            "UserTest",
            "DatabaseConfig"
        ]
        
        for module in valid_modules:
            is_valid, error = is_valid_module_name(module)
            self.assertTrue(is_valid, f"Module {module} should be valid but got error: {error}")
    
    def test_invalid_module_names(self):
        invalid_modules = [
            "",  # Empty name
            "userController",  # Lowercase start
            "User",  # No suffix
            "InvalidModuleName",  # No valid suffix
        ]
        
        for module in invalid_modules:
            is_valid, error = is_valid_module_name(module)
            self.assertFalse(is_valid, f"Module {module} should be invalid but was marked valid")
            self.assertNotEqual("", error, "Error message should not be empty for invalid module")
    
    def test_module_path_inference(self):
        module_paths = {
            "UserController": "app/controllers/",
            "ProductService": "services/",
            "CustomerRepository": "data/repositories/",
            "OrderModel": "models/",
            "LoggingUtil": "utils/",
            "AuthTest": "tests/",
            "DatabaseConfig": "config/"
        }
        
        for module, expected_path in module_paths.items():
            path = get_valid_module_path(module)
            self.assertEqual(expected_path, path, f"Path for {module} should be {expected_path}, got {path}")
    
    def test_layer_inference(self):
        modules = {
            "UserController": "presentation",
            "ProductService": "business_logic",
            "CustomerRepository": "data_access",
            "OrderModel": "model",
            "LoggingUtil": "utility",
            "AuthTest": "testing",
            "DatabaseConfig": "infrastructure"
        }
        
        for module, expected_layer in modules.items():
            layer_info = infer_module_layer(module)
            self.assertEqual(expected_layer, layer_info["layer"], 
                            f"Layer for {module} should be {expected_layer}, got {layer_info['layer']}")
    
    def test_dependency_validation(self):
        # Valid dependencies
        valid_cases = [
            ("UserController", ["UserService", "UserModel", "LoggingUtil"]),
            ("ProductService", ["ProductRepository", "ProductModel", "ValidationUtil"]),
            ("CustomerRepository", ["CustomerModel", "DatabaseUtil"]),
            ("OrderModel", ["ValidationUtil"]),
            ("LoggingUtil", [])
        ]
        
        for module, deps in valid_cases:
            errors = validate_module_dependencies(module, deps)
            self.assertEqual(0, len(errors), 
                            f"Dependencies for {module} should be valid, got errors: {errors}")
        
        # Invalid dependencies
        invalid_cases = [
            ("UserModel", ["UserService"]),  # Model can't depend on Service
            ("LoggingUtil", ["UserController"]),  # Utility can't depend on other layers
            ("ProductRepository", ["UserController"])  # Data access can't depend on Presentation
        ]
        
        for module, deps in invalid_cases:
            errors = validate_module_dependencies(module, deps)
            self.assertGreater(len(errors), 0, 
                              f"Dependencies for {module} should be invalid, but no errors were found")


if __name__ == "__main__":
    unittest.main() 