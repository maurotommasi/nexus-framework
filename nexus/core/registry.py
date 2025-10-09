# framework/core/registry.py

class ComponentRegistry:
    _components = {}
    
    @classmethod
    def register(cls, name, component_class):
        cls._components[name] = component_class
    
    @classmethod
    def get(cls, name):
        return cls._components.get(name)
    
    @classmethod
    def list_components(cls):
        return list(cls._components.keys())