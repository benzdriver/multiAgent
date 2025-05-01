"""
Unified architectural conventions and naming standards template library

This module provides a standardized set of architectural conventions and standards for maintaining consistency across different components (clarifier, validator, fixer, generator).
"""

from pathlib import Path
import json
import re

# Base paths
TEMPLATES_DIR = Path("prompt_templates")
CONFIG_PATH = TEMPLATES_DIR / "config.json"

# Ensure directory exists
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

def get_architecture_conventions():
    """Returns the standard description of system architecture conventions"""
    return """
The system will use the following naming conventions and layer structure:

1. Presentation Layer:
   - Suffixes: Controller, Page, View
   - Responsibility: Handle HTTP requests/responses, UI rendering
   - API Format: HTTP paths (e.g., "GET /api/users")

2. Business Logic Layer:
   - Suffixes: Service
   - Responsibility: Implement business logic
   - API Format: Method names (e.g., "getUserById(id)")

3. Data Access Layer:
   - Suffixes: Repository, DAO
   - Responsibility: Database interaction
   - API Format: Data operation methods (e.g., "findById(id)")

4. Model Layer:
   - Suffixes: Model, Entity, Schema
   - Responsibility: Define data structures
   - API Format: Properties and methods (e.g., "user.getFullName()")

5. Utility Layer:
   - Suffixes: Util, Helper, Client
   - Responsibility: Provide general-purpose functionality
   - API Format: Utility methods (e.g., "formatDate(date)")

6. Testing Layer:
   - Suffixes: Test, Tests, Spec
   - Responsibility: Validate functionality through automated tests
   - Types:
     - Unit Tests: Test individual components in isolation
     - Integration Tests: Test interactions between components
     - E2E Tests: Test complete user flows
   - Target Path: tests/unit/, tests/integration/, tests/e2e/

7. Infrastructure Layer:
   - Suffixes: Config, Module, Pipeline
   - Responsibility: Configure system infrastructure and deployment
   - Target Path: config/, infrastructure/, .github/workflows/
"""

def infer_module_layer(module_name):
    """Infer the architectural layer based on the module name"""
    # Test for presentation layer
    if any(module_name.endswith(suffix) for suffix in ["Controller", "Page", "View"]) or \
       "UI_Components" in module_name or "UI Components" in module_name or \
       "Layout_Components" in module_name or "Layout Components" in module_name or \
       "Pages_-_" in module_name or "Pages - " in module_name:
        domain = extract_domain_from_module_name(module_name) if "_-_" in module_name or " - " in module_name else ""
        return {
            "layer": "presentation",
            "expected_api_format": "HTTP paths",
            "typical_dependencies": ["*Service"],
            "target_path": f"frontend/presentation/{domain}" if domain else (
                "frontend/controllers" if module_name.endswith("Controller") else "frontend/pages"
            )
        }
    
    # Test for business logic layer
    elif module_name.endswith("Service") or \
         "Controllers_-_" in module_name or "Controllers - " in module_name or \
         "Services_-_" in module_name or "Services - " in module_name:
        domain = extract_domain_from_module_name(module_name) if "_-_" in module_name or " - " in module_name else ""
        return {
            "layer": "business",
            "expected_api_format": "method names",
            "typical_dependencies": ["*Repository", "*Client"],
            "target_path": f"backend/business/{domain}" if domain else "backend/services"
        }
    
    # Test for data access layer
    elif any(module_name.endswith(suffix) for suffix in ["Repository", "DAO"]):
        domain = extract_domain_from_module_name(module_name) if "_-_" in module_name or " - " in module_name else ""
        return {
            "layer": "data_access",
            "expected_api_format": "data operations",
            "typical_dependencies": ["*Model", "*Entity"],
            "target_path": f"backend/data/{domain}" if domain else "backend/repositories"
        }
    
    # Test for model layer
    elif any(module_name.endswith(suffix) for suffix in ["Model", "Entity", "Schema"]):
        domain = extract_domain_from_module_name(module_name) if "_-_" in module_name or " - " in module_name else ""
        return {
            "layer": "model",
            "expected_api_format": "properties and methods",
            "typical_dependencies": [],
            "target_path": f"backend/data/{domain}" if domain else "backend/models"
        }
    
    # Test for utility layer
    elif any(module_name.endswith(suffix) for suffix in ["Util", "Helper", "Client"]):
        domain = extract_domain_from_module_name(module_name) if "_-_" in module_name or " - " in module_name else ""
        return {
            "layer": "utility",
            "expected_api_format": "utility methods",
            "typical_dependencies": [],
            "target_path": f"backend/infrastructure/{domain}" if domain else "backend/utils"
        }
    
    # Test for testing layer with more detailed analysis
    elif module_name.endswith("Test") or module_name.endswith("Spec") or "Test" in module_name:
        # Extract the base module name
        base_module = re.sub(r'(Test|Spec|Tests)$', '', module_name)
        base_module = re.sub(r'(Unit|Integration|E2E|System)', '', base_module)
        
        # Determine test type
        test_type = "unit"  # Default
        if "Integration" in module_name:
            test_type = "integration"
        elif "E2E" in module_name or "System" in module_name:
            test_type = "e2e"
        
        # Determine appropriate target path
        if test_type == "unit":
            target_path = f"tests/unit/{base_module.lower()}"
        elif test_type == "integration":
            target_path = f"tests/integration/{base_module.lower()}"
        else:
            target_path = f"tests/e2e/{base_module.lower()}"
        
        return {
            "layer": "testing",
            "test_type": test_type,
            "expected_api_format": "test methods",
            "typical_dependencies": [base_module],
            "target_path": target_path,
            "tests_for": base_module
        }
    
    # Test for infrastructure layer
    elif any(module_name.endswith(suffix) for suffix in ["Config", "Module", "Pipeline"]) or "CI/CD" in module_name:
        return {
            "layer": "infrastructure",
            "expected_api_format": "configuration",
            "typical_dependencies": [],
            "target_path": "config" if module_name.endswith("Config") else (
                ".github/workflows" if "Pipeline" in module_name or "CI/CD" in module_name else "infrastructure"
            )
        }
    
    # Default for unknown modules
    else:
        return {
            "layer": "unknown",
            "expected_api_format": "any",
            "typical_dependencies": [],
            "target_path": "backend/misc"
        }

def get_clarifier_prompt(part_num, total_parts):
    """Returns the module identification prompt template for Clarifier"""
    architecture_conventions = get_architecture_conventions()
    
    return f"""
You are a senior software architect assistant. You are reading part {part_num} of {total_parts} of a system architecture and requirements document.

{architecture_conventions}

Your goal is to identify all modules that are either explicitly described or logically required to implement the system.
This includes not only modules that are directly named, but also any implied components necessary to fulfill the responsibilities.

For example:
- If a document mentions user login, you should generate AuthController, AuthService, and AuthRepository.
- If a document describes data being sent to the backend, you may infer and create DTOs or API handlers.
- If no controller is mentioned for an API, you may still assume one is needed.

For each module, return:
- module_name (following the naming conventions above)
- responsibilities
- key_apis (with appropriate API format based on the layer)
- data_inputs
- data_outputs
- depends_on (list of other module names)
- target_path (suggested relative path)
- layer_type (inferred from the naming)

Additionally, identify testing requirements:
- For each business or data layer module, create corresponding test modules
- For each module, consider what unit tests would be needed
- Identify integration points that require integration tests
- Note any end-to-end scenarios that should be tested
- Create test modules with:
  - module_name: [OriginalModule]Test or [Feature]IntegrationTest 
  - responsibilities: Testing specific aspects of the original module
  - key_apis: Test method names following test framework conventions
  - target_path: tests/unit/, tests/integration/, or tests/e2e/
  - layer_type: "testing"

Also identify infrastructure needs:
- CI/CD pipelines
- Configuration modules
- Deployment scripts

Return the result as a JSON list.
Do NOT return markdown code blocks. DO NOT skip any functionality. Create placeholder modules if unsure.
"""

def get_validator_prompt(part_num, total_parts, boundary_analysis=None):
    """Returns the architecture validation prompt template for Validator"""
    architecture_conventions = get_architecture_conventions()
    
    base_prompt = f"""You are a senior system architect and reviewer.
You are reading part {part_num} of {total_parts} of a combined system architecture and requirements document.

{architecture_conventions}

Please analyze the architecture for coherence, completeness, and quality. Focus on:

1. Whether all required functionality is covered
2. If there are any missing or redundant modules
3. Overlapping responsibilities between modules
4. Undefined dependencies (modules referenced but not defined)
5. Layer structure issues:
   - Whether controllers only depend on service layer, not directly on data access layer
   - Whether services correctly depend on the data access layer
   - Whether API formats conform to the conventions (e.g., controllers use HTTP path format)
6. Test coverage issues:
   - Whether each module has corresponding test modules
   - If all key APIs have test coverage
   - If the appropriate test types (unit, integration, e2e) are defined
7. Provide specific actionable suggestions for improving the architecture
"""

    if boundary_analysis:
        base_prompt += f"""
Additional architectural concerns to address:

Potential module merges to consider:
{json.dumps(boundary_analysis.get('merge_suggestions', []), indent=2)}

Potential module splits to consider:
{json.dumps(boundary_analysis.get('split_suggestions', []), indent=2)}

For overlapping modules, explicitly suggest which ones should be merged or how their responsibilities should be demarcated.
"""

    base_prompt += """
Please return a structured JSON in the following format. DO NOT include explanations outside the JSON structure:

{
  "functional_coverage": {
    "conclusion": "✅ or ❌",
    "explanation": "..."
  },
  "missing_or_redundant_modules": {
    "missing": ["..."],
    "redundant": ["..."]
  },
  "overlapping_responsibilities": ["module A vs module B"],
  "undefined_dependencies": ["moduleX"],
  "layer_violations": ["Controller directly depends on repository", "..."],
  "api_format_issues": ["ServiceX's API format doesn't conform to service layer conventions", "..."],
  "test_coverage_issues": ["Missing tests for UserService", "No integration tests for payment flow"],
  "suggestions": ["..."]
}

Return ONLY the JSON object without any additional text or explanation.
"""
    return base_prompt

def get_fixer_prompt(module_name, issues, original_summary, related_modules=None):
    """Returns the module fixing prompt template for Fixer"""
    architecture_conventions = get_architecture_conventions()
    
    # Infer layer based on module name
    layer_info = infer_module_layer(module_name)
    layer_type = layer_info["layer"]
    expected_api_format = layer_info["expected_api_format"]
    
    # Ensure original summary contains all required fields
    for field in ["responsibilities", "key_apis", "depends_on", "target_path"]:
        if field not in original_summary:
            original_summary[field] = []
    
    # Detect if there's an 'unhashable type: dict' error
    has_dict_error = "unhashable type: 'dict'" in issues
    
    # Custom guidance based on layer type
    layer_specific_guidance = ""
    if layer_type == "testing":
        layer_specific_guidance = """
For test modules, ensure that:
- Test methods follow test framework conventions (like "describe", "it", "test", etc.)
- Target path is correct for the test type (unit, integration, or e2e)
- Dependencies include the module being tested
- Key APIs reflect the test cases needed to validate the original module's functionality
"""
    elif layer_type == "infrastructure":
        layer_specific_guidance = """
For infrastructure modules, ensure that:
- Target path is appropriate for configuration or deployment scripts
- Responsibilities clearly describe the infrastructure concerns
- Dependencies reflect the components that rely on this infrastructure
"""
    
    prompt = f"""You are a senior system architect and fixer specializing in software architecture.

{architecture_conventions}

I need you to fix issues in a module named "{module_name}". This module belongs to the {layer_type} layer, and its API format should be: {expected_api_format}.

## CURRENT SUMMARY
```json
{json.dumps(original_summary, indent=2)}
```

## DETECTED ISSUES
{issues}
"""

    # If there's related modules information, add it to the prompt
    if related_modules:
        prompt += f"""
## RELATED MODULES
```json
{json.dumps(related_modules, indent=2)}
```
"""

    prompt += f"""
## INSTRUCTIONS
Please provide a corrected JSON structure for this module summary that resolves the issues above.

Your response MUST:
1. Be a valid JSON object
2. Include ALL of these required fields with appropriate values (NEVER OMIT ANY FIELD):
   - "module_name": (string) must be "{module_name}"
   - "responsibilities": (array) list of strings describing responsibilities
   - "key_apis": (array) list of API endpoints or methods, format must conform to {layer_type} layer conventions
   - "data_inputs": (array) list of input data types
   - "data_outputs": (array) list of output data types
   - "depends_on": (array) list of dependencies - EMPTY ARRAY ([]) IS VALID if there are no dependencies
   - "target_path": (string) path where module should be placed
   - "layer_type": (string) layer type inferred from naming convention
{"3. IMPORTANT: All values must be simple strings or arrays of strings, NOT nested objects or dictionaries" if has_dict_error else ""}

4. Fix ONLY the issues mentioned, keeping other information intact
5. Ensure your dependencies don't create circular dependencies with related modules
6. Clearly define responsibilities that don't overlap with related modules
7. Ensure controllers only depend on the service layer, services depend on the data access layer, conforming to architectural layering principles
{layer_specific_guidance}

IMPORTANT:
- NEVER omit any required field, even if it's an empty array or string
- Make sure all array fields are valid JSON arrays (e.g., [], ["item1", "item2"])
- Make sure all string fields are valid JSON strings (e.g., "", "some value")
- If a field should be empty, use an empty array [] or empty string "", but DO NOT OMIT THE FIELD

Return ONLY the corrected JSON without any explanation or additional text. Do not include markdown code formatting. Just return the raw JSON object."""
    
    return prompt

def get_generator_prompt(module_summary):
    """Returns the code generation prompt template for Generator"""
    architecture_conventions = get_architecture_conventions()
    
    module_name = module_summary["module_name"]
    responsibilities = module_summary.get("responsibilities", [])
    key_apis = module_summary.get("key_apis", [])
    depends_on = module_summary.get("depends_on", [])
    target_path = module_summary.get("target_path", "")
    
    # Infer layer based on module name
    layer_info = infer_module_layer(module_name)
    layer_type = layer_info["layer"]
    expected_api_format = layer_info["expected_api_format"]
    
    # Special handling for test modules
    if layer_type == "testing":
        test_type = layer_info.get("test_type", "unit")
        tests_for = layer_info.get("tests_for", "")
        
        return f"""You are a testing expert. Please create test files for the **{tests_for}** module using TypeScript and appropriate testing frameworks (Jest, Mocha, or similar).

{architecture_conventions}

## Module Information
- Test Module Name: {module_name}
- Target Path: {target_path}
- Test Type: {test_type}
- Tests for Module: {tests_for}

## Responsibilities of Tests
{chr(10).join(['- ' + r for r in responsibilities])}

## Test Cases to Cover
{chr(10).join(['- ' + api for api in key_apis])}

## Module Dependencies
{chr(10).join(['- ' + dep for dep in depends_on])}

## Task
Generate TypeScript test files that thoroughly test the {tests_for} module.
The implementation should:

1. Follow {test_type} testing best practices
2. Include proper test setup and teardown
3. Use appropriate mocking strategies
4. Test both happy paths and edge cases
5. Use descriptive test names that explain what is being tested

For unit tests: Focus on testing individual functions in isolation
For integration tests: Test interactions between components
For e2e tests: Test complete user flows through the application

Generate only the test code without any explanation.
"""
    
    # Special handling for infrastructure modules
    elif layer_type == "infrastructure":
        return f"""You are a DevOps expert. Please create the infrastructure/configuration file for the **{module_name}** module.

{architecture_conventions}

## Module Information
- Infrastructure Module Name: {module_name}
- Target Path: {target_path}
- Layer Type: {layer_type}

## Responsibilities
{chr(10).join(['- ' + r for r in responsibilities])}

## Key Components
{chr(10).join(['- ' + api for api in key_apis])}

## Task
Generate appropriate configuration/infrastructure code for {module_name}.
This should be:

1. Well-structured and documented
2. Follow best practices for the specific infrastructure tool
3. Include all necessary components described in the responsibilities
4. Be compatible with modern CI/CD environments

Generate only the configuration code without any explanation.
"""
    
    # Standard prompt for normal application modules
    else:
        prompt = f"""You are a senior full-stack developer. Please implement the **{module_name}** module using TypeScript and NestJS.

{architecture_conventions}

## Module Information
- Name: {module_name}
- Target Path: {target_path}
- Layer: {layer_type}
- API Format Convention: {expected_api_format}

## Responsibilities
{chr(10).join(['- ' + r for r in responsibilities])}

## Key APIs (ensure conformity with {layer_type} layer format)
{chr(10).join(['- ' + api for api in key_apis])}

## Dependencies
{chr(10).join(['- ' + dep for dep in depends_on])}

## Task
Generate a TypeScript implementation for the {module_name} module that fulfills all the 
responsibilities and implements all the key APIs.
The implementation should:

1. Conform to the {layer_type} layer architectural conventions
2. Use idiomatic TypeScript with appropriate typing
3. Follow NestJS best practices
4. Ensure API formats conform to the layer's conventions ({expected_api_format})
5. Code should be maintainable, testable, and well-documented

Generate code only for this single module. Return only the code without any explanation.

Remember, corresponding unit test files should be created separately for each module.
"""
        
        return prompt

def get_missing_module_summary_prompt(module_name):
    """Returns the prompt template for generating missing module summaries"""
    architecture_conventions = get_architecture_conventions()
    
    # Infer layer based on module name
    layer_info = infer_module_layer(module_name)
    layer_type = layer_info["layer"]
    expected_api_format = layer_info["expected_api_format"]
    typical_dependencies = layer_info["typical_dependencies"]
    target_path = layer_info["target_path"]
    
    # Special handling for test modules
    if layer_type == "testing":
        test_type = layer_info.get("test_type", "unit")
        tests_for = layer_info.get("tests_for", "")
        
        return f"""You are a TypeScript/NestJS architect specializing in test design.

{architecture_conventions}

You will be given a test module name that was found missing from a system architecture: **{module_name}**.

Based on naming conventions, this module belongs to the testing layer (specifically {test_type} testing), and should test the {tests_for} module.

Please define a JSON summary for the missing test module.
Use this format:

{{
  "module_name": "{module_name}",
  "responsibilities": ["Test the functionality of {tests_for}", "Verify edge cases", "..."],
  "key_apis": ["test{tests_for}Success()", "test{tests_for}EdgeCases()", "..."],
  "data_inputs": ["Test fixtures", "Mock data"],
  "data_outputs": ["Test results"],
  "depends_on": ["{tests_for}"],
  "target_path": "{target_path}",
  "layer_type": "testing",
  "test_type": "{test_type}"
}}

Use placeholder values if necessary. Respond only with JSON. Do NOT add markdown or comments.
"""
    
    # Special handling for infrastructure modules
    elif layer_type == "infrastructure":
        return f"""You are a DevOps and infrastructure expert.

{architecture_conventions}

You will be given an infrastructure module name that was found missing from a system architecture: **{module_name}**.

Based on naming conventions, this module belongs to the infrastructure layer, and should handle system configuration, deployment, or CI/CD processes.

Please define a JSON summary for the missing infrastructure module.
Use this format:

{{
  "module_name": "{module_name}",
  "responsibilities": ["Handle deployment", "Configure system", "..."],
  "key_apis": ["buildStep()", "deployStep()", "..."],
  "data_inputs": ["Source code", "Configuration parameters"],
  "data_outputs": ["Deployed artifacts", "Status reports"],
  "depends_on": [],
  "target_path": "{target_path}",
  "layer_type": "infrastructure"
}}

Use placeholder values if necessary. Respond only with JSON. Do NOT add markdown or comments.
"""
    
    # Standard prompt for normal application modules
    else:
        return f"""You are a TypeScript/NestJS architect.

{architecture_conventions}

You will be given a module name that was found missing from a system architecture: **{module_name}**.

Based on naming conventions, this module belongs to the {layer_type} layer, should use {expected_api_format} format APIs, and typically depends on {', '.join(typical_dependencies)}.

Please define a JSON summary for the missing module.
Use this format:

{{
  "module_name": "{module_name}",
  "responsibilities": ["..."],
  "key_apis": ["..."],  // Ensure API format conforms to {layer_type} layer conventions
  "data_inputs": [],
  "data_outputs": [],
  "depends_on": [],
  "target_path": "{target_path}",
  "layer_type": "{layer_type}"
}}

Use placeholder values if necessary. Respond only with JSON. Do NOT add markdown or comments.
"""

def extract_domain_from_module_name(module_name):
    """从模块名称中提取领域部分，用于构建目录路径
    
    例如：
    - "UI_Components_-_Workspace" -> "workspace"
    - "Controllers - Authentication" -> "authentication"
    """
    domain = ""
    if "_-_" in module_name:
        domain = module_name.split("_-_")[-1]
    elif " - " in module_name:
        domain = module_name.split(" - ")[-1]
    domain = domain.strip().lower()
    return domain

def save_template_config():
    """Save template configuration to the config file"""
    config = {
        "architecture_conventions": {
            "presentation_layer": {
                "suffixes": ["Controller", "Page", "View"],
                "responsibilities": "Handle HTTP requests/responses, UI rendering",
                "api_format": "HTTP paths (e.g., 'GET /api/users')"
            },
            "business_layer": {
                "suffixes": ["Service"],
                "responsibilities": "Implement business logic",
                "api_format": "Method names (e.g., 'getUserById(id)')"
            },
            "data_access_layer": {
                "suffixes": ["Repository", "DAO"],
                "responsibilities": "Database interaction",
                "api_format": "Data operation methods (e.g., 'findById(id)')"
            },
            "model_layer": {
                "suffixes": ["Model", "Entity", "Schema"],
                "responsibilities": "Define data structures",
                "api_format": "Properties and methods (e.g., 'user.getFullName()')"
            },
            "utility_layer": {
                "suffixes": ["Util", "Helper", "Client"],
                "responsibilities": "Provide general-purpose functionality",
                "api_format": "Utility methods (e.g., 'formatDate(date)')"
            },
            "testing_layer": {
                "suffixes": ["Test", "Spec", "Tests"],
                "responsibilities": "Validate functionality through automated tests",
                "subtypes": {
                    "unit": {
                        "target_path": "tests/unit",
                        "focus": "Individual components in isolation"
                    },
                    "integration": {
                        "target_path": "tests/integration",
                        "focus": "Interactions between components"
                    },
                    "e2e": {
                        "target_path": "tests/e2e",
                        "focus": "Complete user flows"
                    }
                }
            },
            "infrastructure_layer": {
                "suffixes": ["Config", "Module", "Pipeline"],
                "responsibilities": "Configure system infrastructure and deployment",
                "target_paths": {
                    "config": "Application configuration",
                    ".github/workflows": "CI/CD pipelines",
                    "infrastructure": "Infrastructure as code"
                }
            }
        }
    }
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

# Ensure config file exists
if not CONFIG_PATH.exists():
    save_template_config()        