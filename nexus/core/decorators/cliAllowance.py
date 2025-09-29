import os

APP_CLI_ENABLED = os.getenv("APP_CLI_ENABLED", None)
APP_CLI_ENABLED = APP_CLI_ENABLED.lower() == "true" if APP_CLI_ENABLED is not None else None

def cli_enabled(func):
    func._is_public = True
    return func

def cli_disabled(func):
    func._is_public = False
    return func

def cli_restricted(default_cli_allowance=cli_disabled):
    """
    Decorator: public only in debug mode.
    If DEBUG is not defined, uses default_decorator (route_public or route_private)
    """
    def decorator(func):
        if APP_CLI_ENABLED is None:
            # DEBUG not set → use passed default decorator
            return default_cli_allowance(func)
        else:
            func._is_public = APP_CLI_ENABLED
            return func
    return decorator
