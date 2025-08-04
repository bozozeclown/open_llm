# core/testing/test_generator.py
import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
import os

class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"

class TestFramework(Enum):
    PYTEST = "pytest"
    UNITTEST = "unittest"
    JEST = "jest"
    MOCHA = "mocha"

@dataclass
class TestCase:
    name: str
    type: TestType
    description: str
    code: str
    dependencies: List[str]
    setup: str
    teardown: str

@dataclass
class TestSuite:
    name: str
    framework: TestFramework
    test_cases: List[TestCase]
    imports: List[str]
    fixtures: List[str]

class TestGenerator:
    def __init__(self):
        self.code_analyzer = AdvancedCodeAnalyzer()
        self.test_templates = self._load_test_templates()
    
    def generate_tests(self, code: str, language: str, test_type: TestType = TestType.UNIT) -> TestSuite:
        """Generate test cases for given code"""
        if language == "python":
            return self._generate_python_tests(code, test_type)
        elif language == "javascript":
            return self._generate_javascript_tests(code, test_type)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def _generate_python_tests(self, code: str, test_type: TestType) -> TestSuite:
        """Generate Python test cases"""
        # Parse the code to extract functions and classes
        try:
            tree = ast.parse(code)
        except SyntaxError:
            raise ValueError("Invalid Python code")
        
        test_cases = []
        
        # Extract functions and classes to test
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        # Generate test cases for functions
        for func in functions:
            test_case = self._generate_function_test(func, code, test_type)
            if test_case:
                test_cases.append(test_case)
        
        # Generate test cases for classes
        for cls in classes:
            class_test_cases = self._generate_class_tests(cls, code, test_type)
            test_cases.extend(class_test_cases)
        
        return TestSuite(
            name=f"test_{test_type.value}",
            framework=TestFramework.PYTEST,
            test_cases=test_cases,
            imports=["pytest", "unittest.mock"],
            fixtures=[]
        )
    
    def _generate_function_test(self, func: ast.FunctionDef, code: str, test_type: TestType) -> Optional[TestCase]:
        """Generate test case for a function"""
        func_name = func.name
        
        # Analyze function to determine test approach
        func_analysis = self._analyze_function(func, code)
        
        # Generate test based on function analysis
        if test_type == TestType.UNIT:
            test_code = self._generate_unit_test(func_name, func_analysis)
        elif test_type == TestType.INTEGRATION:
            test_code = self._generate_integration_test(func_name, func_analysis)
        else:
            test_code = self._generate_functional_test(func_name, func_analysis)
        
        return TestCase(
            name=f"test_{func_name}",
            type=test_type,
            description=f"Test for {func_name} function",
            code=test_code,
            dependencies=func_analysis["dependencies"],
            setup=func_analysis["setup"],
            teardown=func_analysis["teardown"]
        )
    
    def _analyze_function(self, func: ast.FunctionDef, code: str) -> Dict[str, Any]:
        """Analyze function to determine testing approach"""
        analysis = {
            "name": func.name,
            "args": [arg.arg for arg in func.args.args],
            "return_type": self._get_return_type(func),
            "dependencies": [],
            "setup": "",
            "teardown": "",
            "side_effects": False,
            "external_calls": []
        }
        
        # Check for external calls and dependencies
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    analysis["external_calls"].append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    analysis["external_calls"].append(f"{node.func.value.id}.{node.func.attr}")
        
        # Check for side effects
        side_effect_patterns = [
            r'\.write\(',
            r'\.read\(',
            r'\.append\(',
            r'\.remove\(',
            r'\.update\(',
            r'\.delete\(',
            r'print\(',
            r'input\('
        ]
        
        func_code = ast.get_source_segment(code, func)
        for pattern in side_effect_patterns:
            if re.search(pattern, func_code):
                analysis["side_effects"] = True
                break
        
        # Determine dependencies
        if analysis["external_calls"]:
            analysis["dependencies"] = list(set(analysis["external_calls"]))
        
        # Generate setup/teardown if needed
        if analysis["side_effects"]:
            analysis["setup"] = self._generate_setup_code(analysis)
            analysis["teardown"] = self._generate_teardown_code(analysis)
        
        return analysis
    
    def _get_return_type(self, func: ast.FunctionDef) -> str:
        """Extract return type from function"""
        if func.returns:
            return ast.unparse(func.returns)
        
        # Try to infer return type from return statements
        for node in ast.walk(func):
            if isinstance(node, ast.Return) and node.value:
                if isinstance(node.value, ast.Constant):
                    return type(node.value.value).__name__
                elif isinstance(node.value, ast.Name):
                    return "Any"
                elif isinstance(node.value, ast.List):
                    return "List"
                elif isinstance(node.value, ast.Dict):
                    return "Dict"
        
        return "None"
    
    def _generate_unit_test(self, func_name: str, analysis: Dict[str, Any]) -> str:
        """Generate unit test code"""
        test_code = f"""def test_{func_name}():
    # Arrange
    {self._generate_test_setup(analysis)}
    
    # Act
    result = {func_name}({self._generate_test_args(analysis)})
    
    # Assert
    {self._generate_test_assertions(analysis)}
"""
        return test_code
    
    def _generate_integration_test(self, func_name: str, analysis: Dict[str, Any]) -> str:
        """Generate integration test code"""
        test_code = f"""def test_{func_name}_integration():
    # Arrange
    {self._generate_test_setup(analysis)}
    
    # Act
    result = {func_name}({self._generate_test_args(analysis)})
    
    # Assert
    {self._generate_integration_assertions(analysis)}
"""
        return test_code
    
    def _generate_functional_test(self, func_name: str, analysis: Dict[str, Any]) -> str:
        """Generate functional test code"""
        test_code = f"""def test_{func_name}_functional():
    # Arrange
    {self._generate_test_setup(analysis)}
    
    # Act
    result = {func_name}({self._generate_test_args(analysis)})
    
    # Assert
    {self._generate_functional_assertions(analysis)}
"""
        return test_code
    
    def _generate_test_setup(self, analysis: Dict[str, Any]) -> str:
        """Generate test setup code"""
        setup_lines = []
        
        if analysis["setup"]:
            setup_lines.append(analysis["setup"])
        
        # Add mock setup for external dependencies
        for dep in analysis["dependencies"]:
            setup_lines.append(f"mock_{dep} = Mock()")
            setup_lines.append(f"mock_{dep}.return_value = None")
        
        return "\n    ".join(setup_lines) if setup_lines else "pass"
    
    def _generate_test_args(self, analysis: Dict[str, Any]) -> str:
        """Generate test arguments"""
        args = []
        
        for arg in analysis["args"]:
            if arg in ["self", "cls"]:
                continue
            
            # Generate sample values based on argument name
            if "file" in arg.lower():
                args.append('"test_file.txt"')
            elif "path" in arg.lower():
                args.append '"/test/path"'
            elif "url" in arg.lower():
                args.append('"https://example.com"')
            elif "count" in arg.lower() or "num" in arg.lower():
                args.append("10")
            elif "flag" in arg.lower() or "is_" in arg.lower():
                args.append("True")
            else:
                args.append('"test_value"')
        
        return ", ".join(args) if args else ""
    
    def _generate_test_assertions(self, analysis: Dict[str, Any]) -> str:
        """Generate test assertions"""
        assertions = []
        
        return_type = analysis["return_type"]
        
        if return_type == "None":
            assertions.append("# No return value to assert")
        elif return_type in ["int", "float"]:
            assertions.append("assert isinstance(result, (int, float))")
            assertions.append("assert result >= 0")
        elif return_type == "str":
            assertions.append("assert isinstance(result, str)")
            assertions.append("assert len(result) > 0")
        elif return_type == "bool":
            assertions.append("assert isinstance(result, bool)")
        elif return_type == "List":
            assertions.append("assert isinstance(result, list)")
            assertions.append("assert len(result) >= 0")
        elif return_type == "Dict":
            assertions.append("assert isinstance(result, dict)")
            assertions.append("assert len(result) >= 0")
        else:
            assertions.append("assert result is not None")
        
        return "\n    ".join(assertions)
    
    def _generate_integration_assertions(self, analysis: Dict[str, Any]) -> str:
        """Generate integration test assertions"""
        assertions = []
        
        assertions.append("# Integration test assertions")
        assertions.append("assert result is not None")
        
        if analysis["side_effects"]:
            assertions.append("# Verify side effects")
        
        return "\n    ".join(assertions)
    
    def _generate_functional_assertions(self, analysis: Dict[str, Any]) -> str:
        """Generate functional test assertions"""
        assertions = []
        
        assertions.append("# Functional test assertions")
        assertions.append("assert result is not None")
        assertions.append("# Verify expected behavior")
        
        return "\n    ".join(assertions)
    
    def _generate_setup_code(self, analysis: Dict[str, Any]) -> str:
        """Generate setup code for tests with side effects"""
        setup_lines = []
        
        if any(dep in analysis["external_calls"] for dep in ["open", "write", "read"]):
            setup_lines.append("test_file = 'test_temp.txt'")
            setup_lines.append("with open(test_file, 'w') as f:")
            setup_lines.append("    f.write('test content')")
        
        return "\n    ".join(setup_lines)
    
    def _generate_teardown_code(self, analysis: Dict[str, Any]) -> str:
        """Generate teardown code for tests with side effects"""
        teardown_lines = []
        
        if any(dep in analysis["external_calls"] for dep in ["open", "write", "read"]):
            teardown_lines.append("if os.path.exists('test_temp.txt'):")
            teardown_lines.append("    os.remove('test_temp.txt')")
        
        return "\n    ".join(teardown_lines)
    
    def _generate_class_tests(self, cls: ast.ClassDef, code: str, test_type: TestType) -> List[TestCase]:
        """Generate test cases for a class"""
        test_cases = []
        
        # Test class initialization
        test_cases.append(self._generate_class_init_test(cls, code, test_type))
        
        # Test class methods
        methods = [node for node in ast.walk(cls) if isinstance(node, ast.FunctionDef)]
        for method in methods:
            if not method.name.startswith('_'):  # Skip private methods
                test_case = self._generate_method_test(cls, method, code, test_type)
                if test_case:
                    test_cases.append(test_case)
        
        return test_cases
    
    def _generate_class_init_test(self, cls: ast.ClassDef, code: str, test_type: TestType) -> TestCase:
        """Generate test for class initialization"""
        class_name = cls.name
        
        # Get constructor arguments
        init_method = None
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                init_method = node
                break
        
        args = []
        if init_method:
            args = [arg.arg for arg in init_method.args.args if arg.arg != "self"]
        
        test_code = f"""def test_{class_name}_init():
    # Arrange
    {self._generate_test_args_for_class(args)}
    
    # Act
    instance = {class_name}({', '.join(args)})
    
    # Assert
    assert instance is not None
    assert isinstance(instance, {class_name})
"""
        
        return TestCase(
            name=f"test_{class_name}_init",
            type=test_type,
            description=f"Test {class_name} class initialization",
            code=test_code,
            dependencies=[],
            setup="",
            teardown=""
        )
    
    def _generate_method_test(self, cls: ast.ClassDef, method: ast.FunctionDef, code: str, test_type: TestType) -> TestCase:
        """Generate test for class method"""
        class_name = cls.name
        method_name = method.name
        
        # Analyze method
        method_analysis = self._analyze_function(method, code)
        
        # Generate test code
        if test_type == TestType.UNIT:
            test_code = f"""def test_{class_name}_{method_name}():
    # Arrange
    instance = {class_name}()
    {self._generate_test_setup(method_analysis)}
    
    # Act
    result = instance.{method_name}({self._generate_test_args(method_analysis)})
    
    # Assert
    {self._generate_test_assertions(method_analysis)}
"""
        else:
            test_code = f"""def test_{class_name}_{method_name}_{test_type.value}():
    # Arrange
    instance = {class_name}()
    {self._generate_test_setup(method_analysis)}
    
    # Act
    result = instance.{method_name}({self._generate_test_args(method_analysis)})
    
    # Assert
    {self._generate_integration_assertions(method_analysis)}
"""
        
        return TestCase(
            name=f"test_{class_name}_{method_name}",
            type=test_type,
            description=f"Test {class_name}.{method_name} method",
            code=test_code,
            dependencies=method_analysis["dependencies"],
            setup=method_analysis["setup"],
            teardown=method_analysis["teardown"]
        )
    
    def _generate_test_args_for_class(self, args: List[str]) -> str:
        """Generate test arguments for class initialization"""
        arg_values = []
        
        for arg in args:
            if "file" in arg.lower():
                arg_values.append('"test_file.txt"')
            elif "path" in arg.lower():
                arg_values.append '"/test/path"'
            elif "url" in arg.lower():
                arg_values.append('"https://example.com"')
            elif "config" in arg.lower():
                arg_values.append("{{}}")
            else:
                arg_values.append('"test_value"')
        
        return "\n    ".join([f"{arg} = {value}" for arg, value in zip(args, arg_values)])
    
    def run_generated_tests(self, test_suite: TestSuite) -> Dict[str, Any]:
        """Run the generated tests and return results"""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self._generate_test_file(test_suite))
            test_file_path = f.name
        
        try:
            # Run tests using pytest
            result = subprocess.run(
                ["pytest", test_file_path, "-v"],
                capture_output=True,
                text=True
            )
            
            # Parse results
            test_results = {
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "output": result.stdout,
                "errors_output": result.stderr
            }
            
            # Parse pytest output
            for line in result.stdout.split('\n'):
                if "PASSED" in line:
                    test_results["passed"] += 1
                elif "FAILED" in line:
                    test_results["failed"] += 1
                elif "ERROR" in line:
                    test_results["errors"] += 1
            
            return test_results
        
        finally:
            # Clean up temporary file
            os.unlink(test_file_path)
    
    def _generate_test_file(self, test_suite: TestSuite) -> str:
        """Generate complete test file"""
        test_file_content = f"""# Generated tests for {test_suite.name}
import pytest
import unittest.mock
from unittest.mock import Mock
import os
import sys

# Add the source directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the module to test
# from your_module import {', '.join([f.name for f in test_suite.test_cases if 'test_' in f.name])}

"""
        
        # Add test cases
        for test_case in test_suite.test_cases:
            test_file_content += f"\n{test_case.code}\n\n"
        
        return test_file_content
    
    def _load_test_templates(self) -> Dict[str, str]:
        """Load test templates for different languages and frameworks"""
        return {
            "python_pytest_unit": """
def test_{function_name}():
    # Arrange
    {setup}
    
    # Act
    result = {function_name}({args})
    
    # Assert
    {assertions}
""",
            "javascript_jest_unit": """
test('{function_name}', () => {{
    // Arrange
    {setup}
    
    // Act
    const result = {function_name}({args});
    
    // Assert
    {assertions}
}});
"""
        }