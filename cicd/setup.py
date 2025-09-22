from setuptools import setup, find_packages
import json
import os

# Read version from version.json
try:
    version_file = 'version.json'
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            version_data = json.load(f)
            version = version_data.get('version', '0.1.0')  # Default to '0.1.0' if 'version' key is missing
    else:
        version = '0.1.0'  # Fallback version if version.json is missing
except (FileNotFoundError, json.JSONDecodeError) as e:
    version = '0.1.0'  # Fallback version for errors during JSON loading

# Read requirements from requirements.txt
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]

setup(
    name="nexus-framework",
    version=version,
    author="Mauro Tommasi",
    author_email="mauro.tommasi@live.it",
    description="Nexus Framework - A modular and extensible framework for building applications",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "nexus = nexus:main",  
            # maps `nexus` command → main() function inside nexus.py
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",  # Optional: for backward compatibility
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    license="MIT",  # SPDX License expression
    include_package_data=True,
    package_data={
        'framework': ['**/*.py'],
        'config': ['*.py', '*.conf'],
    },
)
