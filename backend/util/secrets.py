import json
import os
import time
from typing import Optional, Dict, Any


class SecretsManager:
    """
    Aina-chan's Secrets Manager! (◕‿◕✿)

    Manages a secrets.json file in the project root directory.
    Handles loading, saving, and accessing configuration values
    like PocketBase address, admin credentials, and more!

    If secrets.json doesn't exist, Aina-chan will create one
    with default values for Senpai to fill in~♪
    """

    def __init__(self, root_dir: Optional[str] = None):
        """
        Initialize the SecretsManager.

        Args:
            root_dir: The project root directory where secrets.json lives.
                      If None, Aina will try to detect it automatically!
        """
        self.root_dir = root_dir or self._find_project_root()
        self.secrets_path = os.path.join(self.root_dir, "secrets.json")
        self._data: Dict[str, Any] = {}
        self._load_or_initialize()

    # --- Project Root Detection ---

    @staticmethod
    def _find_project_root() -> str:
        """
        Aina tries to find the project root directory!

        It looks for common marker files like:
        - pyproject.toml
        - setup.py
        - .git
        - requirements.txt

        If nothing is found, it falls back to the current working directory.
        """
        current_dir = os.getcwd()

        markers = [
            "pyproject.toml",
            "setup.py",
            ".git",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
            "manage.py",
            "app.py",
            "main.py",
        ]

        # Walk up the directory tree looking for marker files
        directory = current_dir
        while True:
            for marker in markers:
                if os.path.exists(os.path.join(directory, marker)):
                    return directory

            parent = os.path.dirname(directory)
            if parent == directory:
                # Reached filesystem root, just use current directory
                return current_dir
            directory = parent

    # --- Default Template ---

    @property
    def _default_template(self) -> Dict[str, Any]:
        """
        The default secrets.json structure!

        Aina-chan made it nice and commented so Senpai knows what to fill in~♪
        """
        return {
            # ─── PocketBase Configuration ───
            "pocketbase": {
                "url": "http://127.0.0.1:8090",      # Your PocketBase server URL
                "admin_email": "",                    # Superadmin email
                "admin_password": "",                 # Superadmin password
                "timeout_seconds": 30,                # Request timeout
            },

            # ─── Application Settings ───
            "app": {
                "name": "My PocketBase App",
                "debug": True,
                "secret_key": "",                     # Generate with: os.urandom(24).hex()
            },

            # ─── Database Sync ───
            "sync": {
                "auto_migrate": True,                  # Auto-create collections on startup?
                "backup_on_migrate": True,             # Backup schema before changes?
                "backup_directory": "./backups",
            },

            # ─── Custom Fields ───
            # Senpai can add anything else here!
            # Aina-chan will preserve all custom keys~ (◕‿◕✿)
        }

    # --- Load / Initialize ---

    def _load_or_initialize(self) -> None:
        """
        Load secrets.json if it exists, otherwise create it with defaults!
        """
        t0 = time.time()
        if os.path.exists(self.secrets_path):
            try:
                with open(self.secrets_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                print(
                    f"Aina-chan loaded secrets from: {self.secrets_path} ✨"
                )
            except (json.JSONDecodeError, IOError) as e:
                print(
                    f"Aina-chan couldn't read secrets.json! "
                    f"Error: {e} (╥﹏╥)"
                )
                print("Aina-chan will create a fresh one~")
                self._data = {}
                self._initialize_defaults()
                self.save()
        else:
            print(
                f"Aina-chan didn't find secrets.json... "
                f"Creating one at: {self.secrets_path} (｀・ω・´)"
            )
            self._initialize_defaults()
            self.save()
        print(f"⏱️ SecretsManager init took {time.time() - t0:.3f}s")

    def _initialize_defaults(self) -> None:
        """Set the internal data to the default template."""
        self._data = self._default_template.copy()

    # --- Save ---

    def save(self) -> bool:
        """
        Save the current data to secrets.json.

        Returns True if successful, False otherwise.
        """
        try:
            os.makedirs(self.root_dir, exist_ok=True)
            with open(self.secrets_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(
                f"Aina-chan couldn't save secrets.json! "
                f"Error: {e} (╥﹏╥)"
            )
            return False

    # --- Accessors ---

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value by its dot-notation key.

        Examples:
            manager.get("pocketbase.url")
            manager.get("pocketbase.admin_email")
            manager.get("app.debug")
            manager.get("nonexistent.key", "fallback")

        Returns the value or default if not found.
        """
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """
        Set a value by its dot-notation key.

        Examples:
            manager.set("pocketbase.url", "http://localhost:8090")
            manager.set("app.debug", False)
            manager.set("custom.my_key", "my_value")

        Args:
            key: Dot-notation key path
            value: The value to set
            save: Whether to immediately save to file

        Returns True if successful.
        """
        keys = key.split(".")
        target = self._data

        # Navigate to the second-to-last key
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]

        # Set the final key
        target[keys[-1]] = value

        if save:
            return self.save()
        return True

    def get_all(self) -> Dict[str, Any]:
        """Get the entire secrets data as a dictionary."""
        return self._data.copy()

    def update(self, data: Dict[str, Any], save: bool = True) -> bool:
        """
        Deep merge a dictionary into the existing secrets.

        This won't overwrite entire sections, just merge them!
        Perfect for adding custom sections without losing existing data.

        Args:
            data: Dictionary to merge in
            save: Whether to immediately save to file

        Returns True if successful.
        """
        self._deep_merge(self._data, data)
        if save:
            return self.save()
        return True

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Recursively merge override dict into base dict.
        """
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                SecretsManager._deep_merge(base[key], value)
            else:
                base[key] = value

    # --- Convenience Properties ---

    @property
    def pocketbase_url(self) -> str:
        """Get the PocketBase server URL."""
        return self.get("pocketbase.url", "http://127.0.0.1:8090")

    @property
    def admin_email(self) -> Optional[str]:
        """Get the superadmin email."""
        email = self.get("pocketbase.admin_email", "")
        return email if email else None

    @property
    def admin_password(self) -> Optional[str]:
        """Get the superadmin password."""
        password = self.get("pocketbase.admin_password", "")
        return password if password else None

    @property
    def is_configured(self) -> bool:
        """
        Check if the essential PocketBase credentials are filled in.

        Aina-chan checks if admin_email and admin_password are non-empty!
        """
        return bool(self.admin_email and self.admin_password)

    # --- Validation ---

    def validate(self) -> Dict[str, bool]:
        """
        Validate the secrets configuration.

        Returns a dictionary with check names and their status.
        """
        checks = {
            "pocketbase_url_set": bool(self.pocketbase_url),
            "admin_email_set": self.admin_email is not None,
            "admin_password_set": self.admin_password is not None,
            "app_secret_key_set": bool(self.get("app.secret_key", "")),
            "debug_mode": bool(self.get("app.debug", False)),
        }

        print("🔍 Aina-chan's Validation Results:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")

        return checks

    # --- Reset ---

    def reset_to_defaults(self) -> bool:
        """
        Reset the entire secrets.json to default values.

        Warning: This will overwrite any existing configuration!
        Aina-chan hopes Senpai knows what they're doing... (◕‿◕;)"""
        self._initialize_defaults()
        return self.save()

    def __repr__(self) -> str:
        """Aina-chan's cute representation of the manager~"""
        configured = "✅ Configured" if self.is_configured else "❌ Not Configured"
        return (
            f"SecretsManager(secrets.json @ {self.root_dir}) {configured}"
        )