from .exceptions import ManifestError
from .linter import lint_manifest
from .json_encoder import json_dumps, json_loads
from .addon import Addon

__all__ = [
    "ManifestError",
    "lint_manifest",
    "json_dumps",
    "json_loads",
    "Addon",
]

__version__ = "0.1.0.dev0"
__copyright__ = "Copyright (c) 2025 AYMENJD"
