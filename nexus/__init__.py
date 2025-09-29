# framework/__init__.py
"""Personal Framework - Cloud, CI/CD, and Infrastructure Management."""

__version__ = "0.1.0"
__author__ = "Muaro Tommasi"
__email__ = "mauro.tommasi@live.it"

from nexus.core.registry import ComponentRegistry
from nexus.core.factory import LayerFactory
from nexus.config.settings import FrameworkConfig

# Register default components
def register_default_components():
    """Register all default framework components."""
    try:
        # Cloud providers
        from nexus.clouds.aws import AWSProvider
        ComponentRegistry.register('cloud_aws', AWSProvider)
    except ImportError:
        pass
    
    try:
        from nexus.clouds.gcp import GCPProvider
        ComponentRegistry.register('cloud_gcp', GCPProvider)
    except ImportError:
        pass
    
    try:
        from nexus.clouds.azure import AzureProvider
        ComponentRegistry.register('cloud_azure', AzureProvider)
    except ImportError:
        pass

# Auto-register on import
register_default_components()