from abc import ABC, abstractmethod

class BaseLayer(ABC):
    def __init__(self, config=None):
        self.config = config or {}
    
    @abstractmethod
    def initialize(self):
        pass
    
    @abstractmethod
    def validate_config(self):
        pass