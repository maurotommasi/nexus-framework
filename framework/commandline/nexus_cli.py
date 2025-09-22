#!/usr/bin/env python3
"""
Nexus CLI Generator - Automatically generate CLI interface for framework functions
Usage: nexus-cli folderA folderB PythonFileWithoutPy ClassName FunctionName param1 value1 param2 value2
"""

import os
import sys
import ast
import importlib
import inspect
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
import json
from dataclasses import dataclass


@dataclass
class FunctionInfo:
    """Information about a discovered function."""
    module_path: str
    file_path: str
    class_name: Optional[str]
    function_name: str
    parameters: List[Dict[str, Any]]
    docstring: Optional[str]
    return_annotation: Optional[str]


class NexusCliGenerator:
    """Automatically generate CLI interface for framework functions."""
    
    def __init__(self, root_folder: str):
        self.root_folder = Path(root_folder).resolve()
        self.discovered_functions: Dict[str, FunctionInfo] = {}
        self.module_cache = {}
        self.cmd_mapping: Dict[str, str] = {}

        # Load command mapping JSON
        mapping_file = self.root_folder / "cmd-mapping.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, "r", encoding="utf-8") as f:
                    self.cmd_mapping = json.load(f)
                print(f"Loaded {len(self.cmd_mapping)} command mappings from {mapping_file}")
            except Exception as e:
                print(f"Warning: Could not load cmd-mapping.json: {e}")
        
    def discover_functions(self) -> Dict[str, FunctionInfo]:
        """Discover all callable functions in the framework."""
        print(f"Scanning {self.root_folder} for Python files...")
        
        for py_file in self.root_folder.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                self._analyze_python_file(py_file)
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}")
                
        print(f"Discovered {len(self.discovered_functions)} callable functions")
        return self.discovered_functions
    
    def _analyze_python_file(self, file_path: Path):
        """Analyze a Python file for callable functions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            relative_path = file_path.relative_to(self.root_folder)
            module_path = str(relative_path.with_suffix('')).replace(os.sep, '.')
            
            # Analyze classes and their methods
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._analyze_class_methods(node, file_path, module_path)
                elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    self._analyze_function(node, file_path, module_path, None)
                    
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _analyze_class_methods(self, class_node: ast.ClassDef, file_path: Path, module_path: str):
        """Analyze methods in a class."""
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                self._analyze_function(node, file_path, module_path, class_node.name)
    
    def _analyze_function(self, func_node: ast.FunctionDef, file_path: Path, 
                         module_path: str, class_name: Optional[str]):
        """Analyze a function node and extract information."""
        try:
            parameters = []
            
            # Extract function parameters
            for arg in func_node.args.args:
                if arg.arg == 'self' or arg.arg == 'cls':
                    continue
                    
                param_info = {
                    'name': arg.arg,
                    'type': None,
                    'default': None,
                    'required': True
                }
                
                # Get type annotation if available
                if arg.annotation:
                    param_info['type'] = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                
                parameters.append(param_info)
            
            # Handle default values
            if func_node.args.defaults:
                num_defaults = len(func_node.args.defaults)
                for i, default in enumerate(func_node.args.defaults):
                    param_idx = len(parameters) - num_defaults + i
                    if param_idx >= 0 and param_idx < len(parameters):
                        parameters[param_idx]['default'] = ast.unparse(default) if hasattr(ast, 'unparse') else str(default)
                        parameters[param_idx]['required'] = False
            
            # Extract docstring
            docstring = None
            if (func_node.body and isinstance(func_node.body[0], ast.Expr) 
                and isinstance(func_node.body[0].value, ast.Constant)):
                docstring = func_node.body[0].value.value
            
            # Extract return annotation
            return_annotation = None
            if func_node.returns:
                return_annotation = ast.unparse(func_node.returns) if hasattr(ast, 'unparse') else str(func_node.returns)
            
            # Create function info
            func_info = FunctionInfo(
                module_path=module_path,
                file_path=str(file_path),
                class_name=class_name,
                function_name=func_node.name,
                parameters=parameters,
                docstring=docstring,
                return_annotation=return_annotation
            )
            
            # Create unique key for the function
            key = f"{module_path}.{class_name}.{func_node.name}" if class_name else f"{module_path}.{func_node.name}"
            self.discovered_functions[key] = func_info
            
        except Exception as e:
            print(f"Error analyzing function {func_node.name}: {e}")
    
    def generate_help(self, search_term: str = None) -> str:
        """Generate help documentation."""
        if not self.discovered_functions:
            self.discover_functions()

        help_text = ["Nexus CLI - Framework Function Executor\n"]
        help_text.append("Usage: nexus-cli <function> [args...]\n")
        help_text.append("Available functions:\n")

        filtered_functions = self.discovered_functions
        if search_term:
            filtered_functions = {k: v for k, v in self.discovered_functions.items() 
                                if search_term.lower() in k.lower() or 
                                    (v.docstring and search_term.lower() in v.docstring.lower())}

        # Reverse mapping for aliases
        alias_to_full = {v: k for k, v in self.cmd_mapping.items()}

        for key, func_info in sorted(filtered_functions.items()):
            display_line = f"  {key}"
            # Check if this function has an alias
            if key in alias_to_full:
                display_line += f" (alias: {alias_to_full[key]})"
            help_text.append(display_line)

            # Show first line of docstring
            if func_info.docstring:
                first_line = func_info.docstring.split('\n')[0].strip()
                help_text.append(f"    {first_line}")

            # Show parameters
            if func_info.parameters:
                param_strs = []
                for param in func_info.parameters:
                    param_str = param['name']
                    if param['type']:
                        param_str += f": {param['type']}"
                    if not param['required'] and param['default']:
                        param_str += f" = {param['default']}"
                    param_strs.append(param_str)
                help_text.append(f"    Parameters: {', '.join(param_strs)}")

            help_text.append("")

        return '\n'.join(help_text)

    
    def parse_command_args(self, args: List[str]) -> Tuple[FunctionInfo, Dict[str, Any]]:
        """Parse command line arguments and return function info and parameters."""
        if len(args) < 2:
            raise ValueError("Not enough arguments. Usage: nexus-cli <module[.Class]> <function> [args...]")

        # Expand alias if present
        first_arg = args[0]
        if first_arg in self.cmd_mapping:
            expanded = self.cmd_mapping[first_arg]
            print(f"Alias detected: '{first_arg}' -> '{expanded}'")
            args[0] = expanded  # Replace with real path

        path_parts = args[0].split(".")
        if len(path_parts) < 1:
            raise ValueError("Invalid module/class path")

        # Decide if last part is a class
        if path_parts[-1][0].isupper():
            class_name = path_parts[-1]
            module_path = ".".join(path_parts[:-1])
        else:
            class_name = None
            module_path = ".".join(path_parts)

        function_name = args[1]
        param_args = args[2:]

        # Build lookup key
        if class_name:
            module_key = f"{module_path}.{class_name}.{function_name}"
        else:
            module_key = f"{module_path}.{function_name}"

        # Discover functions if not cached
        if module_key not in self.discovered_functions:
            if not self.discovered_functions:
                self.discover_functions()
            if module_key not in self.discovered_functions:
                raise ValueError(f"Function '{module_key}' not found.")

        func_info = self.discovered_functions[module_key]

        # Parse parameters: param1 value1 param2 value2 ...
        if len(param_args) % 2 != 0:
            raise ValueError("Parameters must be provided in pairs: param_name param_value")

        parsed_params = {}
        for i in range(0, len(param_args), 2):
            param_name = param_args[i]
            param_value = param_args[i + 1]
            parsed_params[param_name] = self._parse_parameter_value(param_value)

        return func_info, parsed_params

    
    def _parse_parameter_value(self, value: str) -> Any:
        """Parse a parameter value from string to appropriate type."""
        # Try to parse as JSON first for complex types
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        # Try common conversions
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        if value.lower() in ('none', 'null'):
            return None
        
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def execute_function(self, func_info: FunctionInfo, parameters: Dict[str, Any]) -> Any:
        """Execute the specified function with given parameters."""
        # Import the module
        module_path = func_info.module_path
        if module_path not in self.module_cache:
            try:
                # Add the root folder to sys.path temporarily
                if str(self.root_folder) not in sys.path:
                    sys.path.insert(0, str(self.root_folder))
                
                module = importlib.import_module(module_path)
                self.module_cache[module_path] = module
            except ImportError as e:
                raise ImportError(f"Could not import module '{module_path}': {e}")
        
        module = self.module_cache[module_path]
        
        # Get the function or method
        if func_info.class_name:
            # Get class and instantiate it
            if not hasattr(module, func_info.class_name):
                raise AttributeError(f"Class '{func_info.class_name}' not found in module '{module_path}'")
            
            cls = getattr(module, func_info.class_name)
            
            # Check if it's a static method
            func = getattr(cls, func_info.function_name)
            if isinstance(func, staticmethod):
                target_func = func
            else:
                # Instantiate the class
                try:
                    instance = cls()
                    target_func = getattr(instance, func_info.function_name)
                except Exception as e:
                    raise RuntimeError(f"Could not instantiate class '{func_info.class_name}': {e}")
        else:
            # Regular function
            if not hasattr(module, func_info.function_name):
                raise AttributeError(f"Function '{func_info.function_name}' not found in module '{module_path}'")
            
            target_func = getattr(module, func_info.function_name)
        
        # Validate parameters
        sig = inspect.signature(target_func)
        bound_args = sig.bind_partial(**parameters)
        bound_args.apply_defaults()
        
        # Execute the function
        try:
            result = target_func(**bound_args.arguments)
            return result
        except Exception as e:
            raise RuntimeError(f"Error executing function: {e}")
    
    def run_cli(self, args: List[str] = None):
        """Main CLI entry point."""
        if args is None:
            args = sys.argv[1:]
        
        if not args or args[0] in ('-h', '--help', 'help'):
            print(self.generate_help())
            return
        
        if args[0] == 'search' and len(args) > 1:
            print(self.generate_help(args[1]))
            return
        
        if args[0] == 'list':
            if not self.discovered_functions:
                self.discover_functions()
            for key in sorted(self.discovered_functions.keys()):
                print(key)
            return
        
        try:
            func_info, parameters = self.parse_command_args(args)
            
            print(f"Executing: {func_info.module_path}.{func_info.class_name or ''}.{func_info.function_name}")
            print(f"Parameters: {parameters}")
            
            result = self.execute_function(func_info, parameters)
            
            print(f"Result: {result}")
            
            # If result is a complex object, try to format it nicely
            if isinstance(result, (dict, list)):
                print(f"Formatted result:\n{json.dumps(result, indent=2, default=str)}")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    """Main entry point for nexus-cli command."""
    if len(sys.argv) < 2:
        print("Usage: nexus-cli.<command> [args...] or nexus-cli --root <root_folder> <command> [args...]")
        print("Commands: help, search <term>, list, or function execution")
        sys.exit(1)
    
    # Check if --root is specified
    root_folder = os.getcwd()
    args = sys.argv[1:]
    
    if args[0] == '--root' and len(args) > 1:
        root_folder = args[1]
        args = args[2:]
    
    cli = NexusCliGenerator(root_folder)
    cli.run_cli(args)


if __name__ == "__main__":
    main()
