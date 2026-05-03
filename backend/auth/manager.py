import httpx
from typing import Optional
from backend.util.secrets import SecretsManager


class AuthManager:
    """
    Low-level PocketBase API caller for authentication operations.

    - test_connection / check_superuser_exists  → setup
    - login_superuser / login_user              → authentication
    - register_user                             → user creation
    """

    def __init__(self, pb_url: Optional[str] = None):
        self._secrets = SecretsManager()
        self.pb_url = (pb_url or self._secrets.pocketbase_url).rstrip('/')

    # ─── Connection ─────────────────────────────────────────────

    def test_connection(self) -> dict:
        """Check if PocketBase is reachable and return version info."""
        try:
            response = httpx.get(f"{self.pb_url}/api/health", timeout=5)
            response.raise_for_status()
            data = response.json()

            try:
                api_settings = httpx.get(f"{self.pb_url}/api/settings", timeout=5)
                if api_settings.is_success:
                    return {
                        "ok": True,
                        "version": api_settings.json().get("app", {}).get("version", "unknown"),
                    }
            except Exception:
                pass

            return {"ok": True, "version": data.get("version", "unknown")}

        except httpx.ConnectError:
            return {"ok": False, "version": None, "message": "Cannot connect to PocketBase."}
        except httpx.TimeoutException:
            return {"ok": False, "version": None, "message": "Connection timed out."}
        except Exception as e:
            return {"ok": False, "version": None, "message": str(e)}

    def check_superuser_exists(self) -> bool:
        """Check if any superuser has been created."""
        try:
            response = httpx.get(
                f"{self.pb_url}/api/collections/_superusers/records",
                params={"perPage": 1},
                timeout=5,
            )
            if response.is_success:
                data = response.json()
                return data.get("totalItems", 0) > 0
            return False
        except Exception:
            return False

    # ─── Login ──────────────────────────────────────────────────

    def login_superuser(self, email: str, password: str) -> dict:
        """Authenticate as a superuser and return token + record."""
        response = httpx.post(
            f"{self.pb_url}/api/collections/_superusers/auth-with-password",
            json={"identity": email, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def login_user(self, email: str, password: str) -> dict:
        """Authenticate as a regular user and return token + record."""
        response = httpx.post(
            f"{self.pb_url}/api/collections/users/auth-with-password",
            json={"identity": email, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    # ─── Registration ──────────────────────────────────────────

    def register_user(self, username: str, email: str, password: str) -> dict:
        """Register a new user account."""
        response = httpx.post(
            f"{self.pb_url}/api/collections/users/records",
            json={
                "username": username,
                "email": email,
                "password": password,
                "passwordConfirm": password,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
