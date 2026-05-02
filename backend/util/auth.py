"""
Aina-chan's universal PocketBase auth utility! (◕‿◕✿)

Handles authentication for both PocketBase v0.22.x and v0.23+.
"""

from typing import Optional


def authenticate_admin(client, email: str, password: str) -> bool:
    """
    Authenticate as PocketBase superuser/admin.

    Tries the new _superusers method (PB v0.23+) first,
    falls back to old admins method (PB v0.22.x).

    Args:
        client: PocketBase client instance
        email: Admin email
        password: Admin password

    Returns:
        True if authenticated successfully
    """
    # Try new _superusers method (PocketBase v0.23+)
    try:
        client.collection("_superusers").auth_with_password(email, password)
        return True
    except Exception as e:
        error_data = getattr(e, 'data', {})
        status = error_data.get('status', 0) if isinstance(error_data, dict) else 0
        if status != 404:
            # Not a "not found" error — something else went wrong
            raise

    # Fall back to old admins method (PocketBase v0.22.x)
    try:
        client.admins.auth_with_password(email, password)
        return True
    except Exception:
        raise
