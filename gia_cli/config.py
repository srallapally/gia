"""Configuration management for GIA CLI."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigManager:
    """Manage GIA CLI configuration profiles."""
    
    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            config_dir = Path.home() / ".gia"
        
        self.config_dir = Path(config_dir)
        self.config_path = self.config_dir / "config.yaml"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path) as f:
            return yaml.safe_load(f) or {}
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Set restrictive permissions (user read/write only)
        self.config_path.chmod(0o600)
    
    def get_profile(self, profile_name: str = "default") -> Dict[str, str]:
        """Get a specific configuration profile.
        
        Args:
            profile_name: Name of the profile to retrieve
            
        Returns:
            Dictionary with profile configuration
            
        Raises:
            ValueError: If profile doesn't exist or is invalid
        """
        config = self.load_config()
        
        if "profiles" not in config or profile_name not in config["profiles"]:
            raise ValueError(
                f"Profile '{profile_name}' not found. Run 'gia configure' first."
            )
        
        profile = config["profiles"][profile_name]
        
        # Validate required fields
        required = ["base_url", "client_id", "client_secret", "token_endpoint"]
        missing = [field for field in required if field not in profile]
        
        if missing:
            raise ValueError(
                f"Profile '{profile_name}' is missing required fields: {', '.join(missing)}"
            )
        
        return profile
    
    def set_profile(
        self,
        profile_name: str,
        base_url: str,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
        scopes: str | None = None
    ) -> None:
        """Set or update a configuration profile.
        
        Args:
            profile_name: Name of the profile
            base_url: PingOne base URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_endpoint: OAuth2 token endpoint URL
            scopes: Optional OAuth2 scopes
        """
        config = self.load_config()
        
        if "profiles" not in config:
            config["profiles"] = {}
        
        config["profiles"][profile_name] = {
            "base_url": base_url,
            "client_id": client_id,
            "client_secret": client_secret,
            "token_endpoint": token_endpoint,
        }
        
        if scopes:
            config["profiles"][profile_name]["scopes"] = scopes
        
        self.save_config(config)
    
    def list_profiles(self) -> list[str]:
        """List all configured profile names."""
        config = self.load_config()
        return list(config.get("profiles", {}).keys())
    
    def delete_profile(self, profile_name: str) -> None:
        """Delete a configuration profile."""
        config = self.load_config()
        
        if "profiles" in config and profile_name in config["profiles"]:
            del config["profiles"][profile_name]
            self.save_config(config)
        else:
            raise ValueError(f"Profile '{profile_name}' not found")
