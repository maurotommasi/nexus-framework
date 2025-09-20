# config/settings.py
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FrameworkConfig:
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Layer-specific configs
    clouds: Dict[str, Any] = None
    cicd: Dict[str, Any] = None
    management: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.clouds is None:
            self.clouds = {}
        if self.cicd is None:
            self.cicd = {}
        if self.management is None:
            self.management = {}