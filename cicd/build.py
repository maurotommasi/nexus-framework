import os
import shutil
import subprocess
import json
import sys
import argparse
from pathlib import Path

# Default paths
framework_dir = Path('framework')
dist_dir = Path('dist')
zip_dir = Path('releases')
venv_dir = Path('.venv')

# Read version from version.json (if not overridden)
def get_version():
    try:
        version_file = 'version.json'
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                version_data = json.load(f)
                return version_data.get('version', '0.1.0')
        return '0.1.0'
    except (FileNotFoundError, json.JSONDecodeError):
        return '0.1.0'

# Create virtual environment
def create_virtualenv():
    if not venv_dir.exists():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    else:
        print("Virtual environment already exists.")

# Install requirements
def install_requirements():
    print("Installing requirements...")
    pip_executable = venv_dir / ('Scripts' if os.name == 'nt' else 'bin') / 'pip'
    subprocess.check_call([str(pip_executable), "install", "-r", "requirements.txt"])

# Build binary
def build_binary(entry_file, output_name):
    print("Building binary executable using PyInstaller...")
    python_executable = venv_dir / ('Scripts' if os.name == 'nt' else 'bin') / 'python'
    pyinstaller_command = [
        str(python_executable),
        '-m', 'PyInstaller',
        '--onefile',
        '--distpath', str(dist_dir),
        '--name', output_name,
        entry_file
    ]
    subprocess.check_call(pyinstaller_command)

# Create zip file
def create_zip(version, source_dir, zip_name=None):
    zip_filename = zip_name or f"nexus-framework-{version}.zip"
    zip_path = zip_dir / zip_filename
    print(f"Creating zip file: {zip_path}")
    zip_dir.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(str(zip_path).replace('.zip', ''), 'zip', str(source_dir))

# Main build process
def main():
    parser = argparse.ArgumentParser(description="Build Nexus Framework")
    parser.add_argument("--version", help="Specify version (default: read from version.json)", default=None)
    parser.add_argument("--entry", help="Entry point file for PyInstaller", default="framework/cli/main.py")
    parser.add_argument("--name", help="Output binary name", default="nexus-framework")
    parser.add_argument("--zipname", help="Custom zip file name", default=None)

    args = parser.parse_args()

    version = args.version or get_version()
    create_virtualenv()
    install_requirements()

    # Build binary and zip
    build_binary(args.entry, args.name)
    create_zip(version, framework_dir, args.zipname)

    print("\nBuild complete!")
    print(f"Binary executable located at: {dist_dir / (args.name + ('.exe' if os.name == 'nt' else ''))}")
    print(f"Zip archive located at: {zip_dir / (args.zipname or f'nexus-framework-{version}.zip')}")

if __name__ == '__main__':
    main()
