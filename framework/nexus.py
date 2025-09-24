# nexus.py (in root folder)

import sys
import os
from framework.core.decorators.routingAllowance import route_allow_cli_web
from framework.core.decorators.cliAllowance import cli_restricted

# Add framework/cli-gen to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "framework", "commandline"))

from framework.commandline import nexus_cli 

@route_allow_cli_web() # Allow CLI commands in web routes if APP_ROUTE_CLI_WEB is true
@cli_restricted() # Allow CLI commands only if APP_CLI_ENABLED is true
def main():
    nexus_cli.main()

if __name__ == "__main__":
    main()
