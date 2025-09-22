# nexus.py (in root folder)

import sys
import os

# Add framework/cli-gen to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "framework", "commandline"))

from framework.commandline import nexus_cli 

if __name__ == "__main__":
    nexus_cli.main()
