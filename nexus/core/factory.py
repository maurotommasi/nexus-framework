# framework/core/factory.py

#from framework.clouds.aws.ec2 import AWSProvider
#from framework.clouds.gcp.compute import GCPProvider
from nexus.core.registry import ComponentRegistry

class LayerFactory:
    @staticmethod
    def create_cloud_provider(provider_type, **kwargs):
        provider_class = ComponentRegistry.get(f"cloud_{provider_type}")
        if not provider_class:
            raise ValueError(f"Unknown cloud provider: {provider_type}")
        return provider_class(**kwargs)