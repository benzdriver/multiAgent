"""
Module Architecture Validator

This script validates if a given module name adheres to the architecture conventions
defined in the project. It checks for proper naming, proper placement, and dependency rules.
"""

from architecture.module_conventions import infer_module_layer, get_all_architecture_layers, get_layer_by_name


def is_valid_module_name(module_name: str) -> tuple[bool, str]:
    """
    Validates if a module name follows the project's architecture conventions.
    
    Args:
        module_name: The name of the module to validate
        
    Returns:
        A tuple (is_valid, error_message). If the module is valid, 
        is_valid is True and error_message is empty.
    """
    if not module_name:
        return False, "Module name cannot be empty"
    
    if not module_name[0].isupper():
        return False, "Module name must start with an uppercase letter"
    
    module_info = infer_module_layer(module_name)
    
    if module_info["layer"] == "unknown":
        valid_suffixes = []
        for layer in get_all_architecture_layers():
            valid_suffixes.extend(layer["module_types"])
        
        return False, f"Module name must end with one of these suffixes: {', '.join(valid_suffixes)}"
    
    return True, ""


def get_valid_module_path(module_name: str) -> str:
    """
    Returns the valid target path for a module based on architecture conventions.
    
    Args:
        module_name: The name of the module
        
    Returns:
        The target path where the module should be located
    """
    module_info = infer_module_layer(module_name)
    return module_info["target_path"]


def validate_module_dependencies(module_name: str, dependencies: list[str]) -> list[str]:
    """
    Validates if module dependencies adhere to architecture layering rules.
    
    Architecture layer dependencies follow these rules:
    - Presentation can depend on Business and Model
    - Business can depend on Data Access and Model
    - Data Access can only depend on Model
    - Model should not depend on other architecture layers
    - Utility can be used by any layer but should not depend on other layers
    
    Args:
        module_name: The name of the module
        dependencies: List of modules that this module depends on
        
    Returns:
        A list of validation errors, empty if all dependencies are valid
    """
    errors = []
    module_layer = infer_module_layer(module_name)["layer"]
    
    # Define allowed dependencies for each layer
    allowed_dependencies = {
        "presentation": ["presentation", "business_logic", "model", "utility"],
        "business_logic": ["business_logic", "data_access", "model", "utility"],
        "data_access": ["data_access", "model", "utility"],
        "model": ["model", "utility"],
        "utility": ["utility"],
        "testing": ["testing", "presentation", "business_logic", "data_access", "model", "utility"],
        "infrastructure": ["infrastructure", "utility"]
    }
    
    # If layer is unknown, can't validate dependencies
    if module_layer == "unknown":
        errors.append(f"Cannot validate dependencies for module '{module_name}' with unknown layer")
        return errors
    
    # Check each dependency
    for dep in dependencies:
        dep_layer = infer_module_layer(dep)["layer"]
        
        # Skip unknown dependencies
        if dep_layer == "unknown":
            errors.append(f"Dependency '{dep}' has unknown layer")
            continue
        
        # Check if dependency is allowed for this layer
        if dep_layer not in allowed_dependencies.get(module_layer, []):
            errors.append(
                f"Invalid dependency: '{module_name}' ({module_layer}) " +
                f"cannot depend on '{dep}' ({dep_layer})"
            )
    
    return errors


def main():
    """
    Example usage of the module validator.
    """
    test_modules = [
        "UserController",
        "UserService",
        "UserRepository",
        "InvalidModule",
        "UserHelper",
        "ProfilePage",
        "ConfigurationModule"
    ]
    
    print("Module Validation Results:")
    print("==========================")
    
    for module in test_modules:
        is_valid, error = is_valid_module_name(module)
        if is_valid:
            target_path = get_valid_module_path(module)
            print(f"✅ {module}: Valid ({target_path})")
        else:
            print(f"❌ {module}: {error}")
    
    print("\nDependency Validation Example:")
    print("==============================")
    
    # Example dependency validation
    service_deps = ["UserRepository", "UserModel", "LoggerUtil"]
    errors = validate_module_dependencies("UserService", service_deps)
    
    if errors:
        print(f"❌ Dependencies for UserService have issues:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"✅ All dependencies for UserService are valid")


if __name__ == "__main__":
    main() 