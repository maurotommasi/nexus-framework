import argparse
import importlib
import inspect
import sys
import json
from pathlib import Path


class NexusPackageCLI:
    def __init__(self, base_package: str = "framework"):
        self.base_package = base_package

    def _convert_type(self, value: str):
        """Try to auto-convert CLI values to int, float, bool, JSON, or leave as str"""
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        try:
            return json.loads(value)
        except Exception:
            return value

    def run(self, argv):
        parser = argparse.ArgumentParser(description="Nexus Package CLI")
        parser.add_argument("folders", nargs="+", help="Module path inside the framework package")
        parser.add_argument("className", help="Class name inside the module")
        parser.add_argument("functionName", help="Function/method name inside the class")
        parser.add_argument("params", nargs="*", help="Positional parameters for the function")

        args = parser.parse_args(argv)

        # Build module path (e.g. framework.clouds_folder.aws_folder.ec2_python_code_dot_py)
        module_path = ".".join([self.base_package] + args.folders)
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(f"Could not import module: {module_path}") from e

        # Get class
        if not hasattr(module, args.className):
            raise AttributeError(f"Class {args.className} not found in {module_path}")
        cls = getattr(module, args.className)
        instance = cls()

        # Get function
        if not hasattr(instance, args.functionName):
            raise AttributeError(f"Function {args.functionName} not found in class {args.className}")
        func = getattr(instance, args.functionName)

        # Convert parameters
        sig = inspect.signature(func)
        bound_args = []
        for param, value in zip(sig.parameters.values(), args.params):
            bound_args.append(self._convert_type(value))

        # Execute function
        result = func(*bound_args)
        if result is not None:
            print("Result:", result)



# To run from command line:
# python nexus.py clouds_folder aws_folder ec2_python_code_dot_py EC2PythonCode deploy_instance '{"instance_type": "t2.micro", "region": "us-west-2"}'
# This would call:  EC2PythonCode().deploy_instance({"instance_type": "t2.micro", "region": "us-west-2"})
# Adjust the command above based on your actual module and class names.