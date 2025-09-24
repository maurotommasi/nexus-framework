import os

APP_ROUTE_ENABLED = os.getenv("APP_ROUTE_ENABLED", None)
APP_ROUTE_ENABLED = APP_ROUTE_ENABLED.lower() == "true" if APP_ROUTE_ENABLED is not None else None

APP_CLI_WEB = os.getenv("APP_ROUTE_CLI_WEB", "false").lower() == "true"

def route_public(func):
    func._is_public = True
    return func

def route_private(func):
    func._is_public = False
    return func

def route_restricted(default_route_allowance=route_private):
    """
    Decorator: public only in debug mode.
    If DEBUG is not defined, uses default_decorator (route_public or route_private)
    """
    def decorator(func):
        if APP_ROUTE_ENABLED is None:
            # DEBUG not set → use passed default decorator
            return default_route_allowance(func)
        else:
            func._is_public = APP_ROUTE_ENABLED
            return func
    return decorator

def route_allow_cli_web(func):
    func._is_public = APP_CLI_WEB
    return func
