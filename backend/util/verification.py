import httpx
from typing import Optional
from backend.util.secrets import SecretsManager


class VerifyIdentity:
    """
    Aina-chan's standalone Identity Verifier! (◕‿◕✿)

    This class can verify identity using:
    - JWT token → returns user data if valid
    - email + password → checks credentials and returns user data
    - refresh tokens → gives you a shiny new token

    It is independent of AuthManager – any part of the app can use it!
    """

    def __init__(self, pb_url: Optional[str] = None):
        self._secrets = SecretsManager()
        self.pb_url = (pb_url or self._secrets.pocketbase_url).rstrip('/')

    def _headers(self, token: Optional[str] = None) -> dict:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    # ─── Verify by Token ────────────────────────────────────────
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verifies a JWT token and returns the associated user info.
        Tries superuser collection first, then regular users.
        Returns None if token is invalid/expired.
        """
        headers = self._headers(token)

        # Try superuser
        try:
            resp = httpx.get(
                f"{self.pb_url}/api/collections/_superusers/records",
                headers=headers,
                params={"perPage": 1},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    user = items[0]
                    user["_collection"] = "_superusers"
                    return user
        except Exception as e:
            print(e)
            pass

        # Try regular users
        try:
            resp = httpx.get(
                f"{self.pb_url}/api/collections/users/records",
                headers=headers,
                params={"perPage": 1},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    user = items[0]
                    user["_collection"] = "users"
                    return user
        except Exception as e:
            print(e)
            pass

        return None

    # ─── Verify by Credentials ──────────────────────────────────
    def verify_credentials(self, email: str, password: str) -> Optional[dict]:
        """
        Checks if the given email and password are valid.
        Returns the user info (without token) if valid.
        Tries superuser collection first, then regular users.
        """
        # Try superuser
        try:
            resp = httpx.post(
                f"{self.pb_url}/api/collections/_superusers/auth-with-password",
                json={"identity": email, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                user = data.get("record", {})
                user["_collection"] = "_superusers"
                return user
        except Exception:
            pass

        # Try regular users
        try:
            resp = httpx.post(
                f"{self.pb_url}/api/collections/users/auth-with-password",
                json={"identity": email, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                user = data.get("record", {})
                user["_collection"] = "users"
                return user
        except Exception:
            pass

        return None

    # ─── Refresh Token ──────────────────────────────────────────
    def refresh_token(self, token: str) -> Optional[dict]:
        """
        Refreshes the given auth token.
        Returns new token data (token, record, etc.) or None.
        Tries superuser first, then regular users.
        """
        headers = self._headers(token)

        # Try superuser
        try:
            resp = httpx.post(
                f"{self.pb_url}/api/collections/_superusers/auth-refresh",
                headers=headers,
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                data["_collection"] = "_superusers"
                return data
        except Exception:
            pass

        # Try regular users
        try:
            resp = httpx.post(
                f"{self.pb_url}/api/collections/users/auth-refresh",
                headers=headers,
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                data["_collection"] = "users"
                return data
        except Exception:
            pass

        return None

    # ─── Check if Token is Still Valid (lightweight) ────────────
    def is_token_valid(self, token: str) -> bool:
        """Return True if the token is valid, False otherwise."""
        return self.verify_token(token) is not None

    # ─── Get User from an Identity (token OR email+password) ────
    def verify_identity(
        self,
        *,
        token: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Unified method: pass either a `token` OR `email`+`password`.
        Returns user info dict or None.
        """
        if token:
            return self.verify_token(token)
        elif email and password:
            return self.verify_credentials(email, password)
        else:
            raise ValueError(
                "Aina-chan needs either a token or email+password to verify identity! (╥﹏╥)"
            )
