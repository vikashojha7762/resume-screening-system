"""
Model Registry for version management and model loading
"""
import logging
import pickle
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for managing ML model versions"""
    
    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.registry_path / "registry.json"
        self.models: Dict[str, Dict[str, Any]] = {}
        self.load_registry()
    
    def load_registry(self) -> None:
        """Load model registry from disk"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    self.models = json.load(f)
                logger.info(f"Loaded {len(self.models)} models from registry")
            except Exception as e:
                logger.error(f"Error loading registry: {str(e)}")
                self.models = {}
        else:
            self.models = {}
    
    def save_registry(self) -> None:
        """Save model registry to disk"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.models, f, indent=2)
            logger.info("Registry saved successfully")
        except Exception as e:
            logger.error(f"Error saving registry: {str(e)}")
    
    def register_model(
        self,
        model_name: str,
        model_path: str,
        version: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a new model version"""
        if model_name not in self.models:
            self.models[model_name] = {}
        
        self.models[model_name][version] = {
            'path': model_path,
            'registered_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'is_active': False
        }
        
        # Set as active if first version
        if len(self.models[model_name]) == 1:
            self.set_active_version(model_name, version)
        
        self.save_registry()
        logger.info(f"Registered model {model_name} version {version}")
    
    def set_active_version(self, model_name: str, version: str) -> None:
        """Set active version for a model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found in registry")
        
        if version not in self.models[model_name]:
            raise ValueError(f"Version {version} not found for model {model_name}")
        
        # Deactivate all versions
        for v in self.models[model_name]:
            self.models[model_name][v]['is_active'] = False
        
        # Activate specified version
        self.models[model_name][version]['is_active'] = True
        self.save_registry()
        logger.info(f"Set active version {version} for model {model_name}")
    
    def get_active_version(self, model_name: str) -> Optional[str]:
        """Get active version for a model"""
        if model_name not in self.models:
            return None
        
        for version, info in self.models[model_name].items():
            if info.get('is_active'):
                return version
        
        return None
    
    def get_model_path(self, model_name: str, version: Optional[str] = None) -> Optional[str]:
        """Get path to model file"""
        if model_name not in self.models:
            return None
        
        if version is None:
            version = self.get_active_version(model_name)
            if version is None:
                return None
        
        if version not in self.models[model_name]:
            return None
        
        return self.models[model_name][version]['path']
    
    def list_models(self) -> Dict[str, Any]:
        """List all registered models"""
        return {
            name: {
                'versions': list(versions.keys()),
                'active_version': self.get_active_version(name)
            }
            for name, versions in self.models.items()
        }


# Singleton instance
model_registry = ModelRegistry()

