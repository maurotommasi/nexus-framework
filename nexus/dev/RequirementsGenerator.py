import os
import ast
import subprocess

class RequirementsGenerator:
    def __init__(self, project_dir, output_file='requirements.txt'):
        """Initializes the RequirementsGenerator class.
        
        Args:
            project_dir (str): Path to the project directory.
            output_file (str): Path to the output requirements.txt file.
        """
        self.project_dir = project_dir
        self.output_file = output_file
        self.package_dict = self.get_installed_packages()

    def get_installed_packages(self):
        """Returns a dictionary of installed packages and their versions."""
        installed_packages = subprocess.check_output(['pip', 'freeze']).decode().splitlines()
        package_dict = {}
        for package in installed_packages:
            name, version = package.split('==')
            package_dict[name.lower()] = version
        return package_dict

    def extract_imports_from_file(self, file_path):
        """Extracts imported libraries from a Python file.

        Args:
            file_path (str): Path to the Python file.

        Returns:
            set: A set of package names imported in the file.
        """
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        imports.add(node.module)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
        return imports

    def generate_requirements_txt(self):
        """Generates a requirements.txt file by scanning the project directory."""
        all_imports = set()

        # Walk through the project directory and extract imports
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(".py"):  # Only process Python files
                    file_path = os.path.join(root, file)
                    imports = self.extract_imports_from_file(file_path)
                    all_imports.update(imports)

        # Filter out only the packages that are installed
        requirements = []
        for package in all_imports:
            package_lower = package.lower()
            if package_lower in self.package_dict:
                requirements.append(f"{package}=={self.package_dict[package_lower]}")

        # Write the requirements to the output file
        with open(self.output_file, 'w', encoding='utf-8') as req_file:
            req_file.write("\n".join(requirements))

        print(f"requirements.txt generated successfully in {self.output_file}")

# Main function to run the script
def main():
    project_dir = input("Enter the path to the project directory: ")
    output_file = input("Enter the name of the output requirements.txt file (default: requirements.txt): ") or 'requirements.txt'
    
    generator = RequirementsGenerator(project_dir, output_file)
    generator.generate_requirements_txt()

if __name__ == "__main__":
    main()