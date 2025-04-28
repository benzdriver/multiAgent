"""
Module Conventions

This module defines the architectural conventions for module naming and organization.
It provides functions to retrieve conventions and determine which layer a module belongs to.
This is used for programmatic validation of module names, paths, and dependencies.
"""

from typing import List, Dict

# Define the architecture layers with their conventions
ARCHITECTURE_LAYERS = [
    {
        "layer": "presentation",
        "module_types": ["Controller", "Page", "View", "Component"],
        "responsibilities": "Handle user interaction, input validation, and response formatting",
        "api_format": "REST/GraphQL endpoints, UI components",
        "target_path": "app/controllers/"
    },
    {
        "layer": "business_logic",
        "module_types": ["Service", "Manager", "Orchestrator", "Processor"],
        "responsibilities": "Implement business rules, orchestrate operations",
        "api_format": "Method calls with domain objects",
        "target_path": "services/"
    },
    {
        "layer": "data_access",
        "module_types": ["Repository", "DAO", "Store", "Persistence"],
        "responsibilities": "Data access, storage, and retrieval",
        "api_format": "CRUD operations, query methods",
        "target_path": "data/repositories/"
    },
    {
        "layer": "model",
        "module_types": ["Model", "Entity", "DTO", "Schema"],
        "responsibilities": "Define data structures and domain objects",
        "api_format": "Properties, minimal behavior",
        "target_path": "models/"
    },
    {
        "layer": "utility",
        "module_types": ["Util", "Helper", "Utils", "Common"],
        "responsibilities": "Provide shared functionality and utilities",
        "api_format": "Static utility methods",
        "target_path": "utils/"
    },
    {
        "layer": "testing",
        "module_types": ["Test", "Mock", "Fixture", "TestCase"],
        "responsibilities": "Test application components",
        "api_format": "Test methods",
        "target_path": "tests/"
    },
    {
        "layer": "infrastructure",
        "module_types": ["Config", "Module", "Provider", "Factory"],
        "responsibilities": "Configure system components and infrastructure",
        "api_format": "Configuration methods",
        "target_path": "config/"
    }
]

# Module types for each layer
LAYER_MODULE_TYPES = {
    "presentation": [
        "controller", "view", "middleware", "validator", "dto", "api"
    ],
    "business": [
        "service", "manager", "workflow", "factory", "provider"
    ],
    "data": [
        "repository", "model", "entity", "dao", "store"
    ],
    "infrastructure": [
        "config", "util", "helper", "exception", "constant", "logging", "security"
    ],
    "testing": [
        "unit_test", "integration_test", "system_test", "mock", "fixture", "test_util"
    ]
}

# Domains examples
DOMAIN_EXAMPLES = [
    "user", "auth", "product", "order", "payment", "notification", 
    "inventory", "shipping", "billing", "report", "admin", "search",
    "recommendation", "analytics", "message"
]

# Testing conventions
TESTING_CONVENTIONS = {
    "unit_test": {
        "naming_convention": "{module_name}_test.py or test_{module_name}.py",
        "description": "Tests for individual components in isolation",
        "target_modules": ["service", "repository", "controller", "util", "helper"]
    },
    "integration_test": {
        "naming_convention": "{module_name}_integration_test.py",
        "description": "Tests for interactions between components",
        "target_layers": ["business", "data", "presentation"]
    },
    "system_test": {
        "naming_convention": "{feature}_system_test.py",
        "description": "End-to-end tests for complete features",
        "scope": "Cross-layer functionality"
    }
}

def get_all_architecture_layers() -> list[dict]:
    """
    Returns all architecture layers with their conventions.
    
    Returns:
        A list of dictionaries, each representing an architecture layer
    """
    return ARCHITECTURE_LAYERS

def infer_module_layer(module_name: str) -> dict:
    """
    Infers which architecture layer a module belongs to based on its name.
    
    Args:
        module_name: The name of the module
        
    Returns:
        A dictionary with layer information, or unknown if no match found
    """
    for layer in ARCHITECTURE_LAYERS:
        for suffix in layer["module_types"]:
            if module_name.endswith(suffix):
                return {
                    "layer": layer["layer"],
                    "module_type": suffix,
                    "target_path": layer["target_path"],
                    "responsibilities": layer["responsibilities"]
                }
    
    # If no matching suffix was found
    return {
        "layer": "unknown",
        "module_type": "unknown",
        "target_path": "unknown",
        "responsibilities": "unknown"
    }

def get_layer_by_name(layer_name: str) -> dict:
    """
    Retrieves layer information by its name.
    
    Args:
        layer_name: The name of the layer (e.g., 'presentation', 'business_logic')
        
    Returns:
        Layer information as a dictionary, or None if not found
    """
    for layer in ARCHITECTURE_LAYERS:
        if layer["layer"] == layer_name:
            return layer
    return None

def get_layer_by_module_type(module_type: str) -> str:
    """
    Get the layer name based on the module type
    
    Args:
        module_type: The type of module
        
    Returns:
        The layer name the module belongs to
    """
    for layer, module_types in LAYER_MODULE_TYPES.items():
        if module_type in module_types:
            return layer
    return "unknown"

def get_all_module_types() -> List[str]:
    """
    Get all possible module types across all layers
    
    Returns:
        List of all module types
    """
    all_types = []
    for layer, module_types in LAYER_MODULE_TYPES.items():
        all_types.extend(module_types)
    return all_types

def get_architecture_info() -> Dict:
    """
    Get comprehensive architecture information
    
    Returns:
        Dict with all architecture conventions
    """
    return {
        "layers": ARCHITECTURE_LAYERS,
        "layer_module_types": LAYER_MODULE_TYPES,
        "domain_examples": DOMAIN_EXAMPLES,
        "testing_conventions": TESTING_CONVENTIONS
    } 