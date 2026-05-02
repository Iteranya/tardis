import httpx
from typing import Optional
from backend.util.secrets import SecretsManager


class AuthManager:
    """
    Aina-chan's Auth Manager! (◕‿◕✿)

    Handles direct PocketBase operations for authentication
    and setup. Uses httpx to avoid Python SDK parsing issues.
    """

    def __init__(self, pb_url: Optional[str] = None):
        self._secrets = SecretsManager()
        self.pb_url = pb_url or self._secrets.pocketbase_url

    def _headers(self, token: Optional[str] = None) -> dict:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    # ─── Connection ───

    def test_connection(self) -> dict:
        """Check if PocketBase is reachable and return version info."""
        try:
            response = httpx.get(f"{self.pb_url}/api/health", timeout=5)
            response.raise_for_status()
            data = response.json()

            # Try to get version from API settings
            try:
                api_settings = httpx.get(f"{self.pb_url}/api/settings", timeout=5)
                if api_settings.ok:
                    return {
                        "ok": True,
                        "version": api_settings.json().get("app", {}).get("version", "unknown"),
                    }
            except Exception:
                pass

            return {"ok": True, "version": data.get("version", "unknown")}

        except httpx.ConnectError:
            return {"ok": False, "version": None, "message": "Cannot connect to PocketBase. Make sure it's running."}
        except httpx.TimeoutException:
            return {"ok": False, "version": None, "message": "Connection timed out. Check the URL and firewall."}
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
            if response.ok:
                data = response.json()
                return data.get("totalItems", 0) > 0
            return False
        except Exception:
            return False

    # ─── Superuser Management ───

    def create_superuser(self, email: str, password: str) -> dict:
        """
        Create the initial superuser.

        Only works if NO superuser exists yet (PocketBase restriction).
        """
        response = httpx.post(
            f"{self.pb_url}/api/collections/_superusers/records",
            json={
                "email": email,
                "password": password,
                "passwordConfirm": password,
            },
            timeout=10,
        )

        if response.status_code == 403:
            # Superuser already exists
            data = response.json()
            raise PermissionError(data.get("message", "A superuser already exists!"))

        response.raise_for_status()
        return response.json()

    def login_superuser(self, email: str, password: str) -> dict:
        """Authenticate as a superuser."""
        response = httpx.post(
            f"{self.pb_url}/api/collections/_superusers/auth-with-password",
            json={"identity": email, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    # ─── Regular User Management ───

    def login_user(self, email: str, password: str) -> dict:
        """Authenticate as a regular user."""
        response = httpx.post(
            f"{self.pb_url}/api/collections/users/auth-with-password",
            json={"identity": email, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

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

    def get_user_by_token(self, token: str) -> Optional[dict]:
        """Get user info from a JWT token (works for both superusers and regular users)."""
        headers = self._headers(token)

        # Try superuser first
        try:
            response = httpx.get(
                f"{self.pb_url}/api/collections/_superusers/records",
                headers=headers,
                params={"perPage": 1},
                timeout=5,
            )
            if response.ok:
                data = response.json()
                items = data.get("items", [])
                if items:
                    user = items[0]
                    user["is_superuser"] = True
                    return user
        except Exception:
            pass

        # Try regular user
        try:
            response = httpx.get(
                f"{self.pb_url}/api/collections/users/records",
                headers=headers,
                params={"perPage": 1},
                timeout=5,
            )
            if response.ok:
                data = response.json()
                items = data.get("items", [])
                if items:
                    user = items[0]
                    user["is_superuser"] = False
                    return user
        except Exception:
            pass

        return None

    # ─── Token Refresh ───

    def refresh_token(self, token: str) -> Optional[dict]:
        """Refresh an auth token."""
        headers = self._headers(token)

        # Try superuser
        try:
            response = httpx.post(
                f"{self.pb_url}/api/collections/_superusers/auth-refresh",
                headers=headers,
                timeout=5,
            )
            if response.ok:
                return response.json()
        except Exception:
            pass

        # Try regular user
        try:
            response = httpx.post(
                f"{self.pb_url}/api/collections/users/auth-refresh",
                headers=headers,
                timeout=5,
            )
            if response.ok:
                return response.json()
        except Exception:
            pass

        return None
