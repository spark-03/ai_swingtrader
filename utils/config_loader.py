import json
import yaml
from pathlib import Path
from typing import Any, Dict


class ConfigLoader:
    """Load configuration files (YAML or JSON) with optional defaults.

    Parameters
    ----------
    config_path: str | Path
        Path to the configuration file.
    defaults: dict | None
        Optional dictionary of default values that are merged into the loaded config.
    """

    def __init__(self, config_path: str | Path, defaults: Dict[str, Any] | None = None):
        self.config_path = Path(config_path)
        self.defaults = defaults or {}
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Read the file and populate ``self.config``.
        Supports ``.yaml``/``.yml`` and ``.json`` extensions.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        if self.config_path.suffix in {".yaml", ".yml"}:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        elif self.config_path.suffix == ".json":
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise ValueError("Unsupported config file type. Use .yaml/.yml or .json")

        # Merge defaults (user‑provided defaults take precedence over file values)
        self.config = {**data, **self.defaults}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value.
        If the key is missing, ``default`` is returned (or ``None``).
        """
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.config[key]

    def __repr__(self) -> str:
        return f"ConfigLoader(path={self.config_path}, keys={list(self.config.keys())})"
