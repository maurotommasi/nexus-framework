import os
import subprocess
import sys
from pathlib import Path

# Path to your virtual environment directory
venv_dir = Path('.venv')

def create_virtualenv():
    """Create a virtual environment if it doesn't exist."""
    if not venv_dir.exists():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    else:
        print("Virtual environment already exists.")

def install_requirements():
    """Install the necessary requirements using pip."""
    print("Installing requirements...")
    subprocess.check_call([str(venv_dir / 'Scripts' / 'pip'), "install", "--upgrade", "pip", "setuptools", "pyinstaller"])

def print_activation_instruction():
    """Print instructions for activating the virtual environment."""
    print("\nTo activate the virtual environment, use the following command:")
    if os.name == 'nt':  # Windows
        print(f"  {venv_dir / 'Scripts' / 'activate'}")
    else:  # Unix-based (macOS/Linux)
        print(f"  source {venv_dir / 'bin' / 'activate'}")

def main():
    """Main function to create virtual environment, install dependencies, and show activation command."""
    create_virtualenv()
    install_requirements()

    # Print the activation instructions
    print_activation_instruction()

if __name__ == '__main__':
    main()

