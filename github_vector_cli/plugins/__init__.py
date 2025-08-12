from typing import Dict, Any
import importlib
import pkgutil
from pathlib import Path
from github_vector_cli.plugins import search

def load_plugins(app) -> Dict[str, Any]:
    """Load all plugins and register their commands"""
    plugin_dir = Path(__file__).parent
    plugins = {}
    
    for _, name, _ in pkgutil.iter_modules([str(plugin_dir)]):
        if name == "__init__":
            continue
        
        try:
            module = importlib.import_module(f"github_vector_cli.plugins.{name}")
            if hasattr(module, "register_plugin"):
                module.register_plugin(app)
                plugins[name] = module
        except ImportError as e:
            print(f"[yellow]Warning: Could not load plugin {name}: {e}")
    
    return plugins