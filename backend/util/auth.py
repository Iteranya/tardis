from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.auth.manager import AuthManager
from backend.auth.service import AuthService
from backend.util.secrets import get_secrets

_auth_service_instance = None

def get_auth_service() -> AuthService:
    global _auth_service_instance
    if _auth_service_instance is None:
        print("⚡ [ROUTER] Creating NEW AuthService instance (first time only!)")
        _auth_service_instance = AuthService()
    return _auth_service_instance

def authenticate_admin(client, email: str, password: str) -> bool:
    print(f"\n🔐 [DEPENDS authenticate_admin] Attempting auth for {email}")
    try:
        client.collection("_superusers").auth_with_password(email, password)
        print("✅ [DEPENDS] Superuser auth success (new method)!")
        return True
    except Exception as e:
        error_data = getattr(e, 'data', {})
        status_code = error_data.get('status', 0) if isinstance(error_data, dict) else 0
        print(f"❌ [DEPENDS] New method failed with status {status_code}: {e}")
        if status_code != 404:
            raise  # Not a "not found" error, something else

    try:
        client.admins.auth_with_password(email, password)
        print("✅ [DEPENDS] Superuser auth success (old method)!")
        return True
    except Exception as e:
        print(f"❌ [DEPENDS] Old method also failed: {e}")
        raise


security = HTTPBearer(auto_error=False)


async def get_current_superuser(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    print("\n" + "=" * 60)
    print("🛡️ [DEPENDS get_current_superuser] CALLED")
    print(f"🔶 Credentials object: {credentials}")

    if not credentials:
        print("🚫 [DEPENDS] No credentials object at all!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    print(f"🔑 [DEPENDS] Token: {token[:50]}... (len={len(token)})")

    # Load secrets
    secrets = get_secrets()
    print(f"📂 [DEPENDS] SecretsManager created.")
    pb_url = getattr(secrets, 'pocketbase_url', None)
    print(f"🌐 [DEPENDS] PocketBase URL from secrets: {pb_url}")

    if not pb_url:
        print("💥 [DEPENDS] CRITICAL: PocketBase URL is None/Empty!")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: PocketBase URL not set."
        )

    manager = AuthManager(pb_url=pb_url)
    print(f"👮 [DEPENDS] AuthManager created. URL: {manager.pb_url}")

    user = manager.get_user_by_token(token)
    print(f"👤 [DEPENDS] User from manager: {user}")

    if user:
        print(f"   🆔 ID: {user.get('id')}")
        print(f"   📧 Email: {user.get('email')}")
        print(f"   👑 is_superuser: {user.get('is_superuser')}")
        print(f"   🔑 User keys: {user.keys()}")

    if not user:
        print("🚫 [DEPENDS] No user found for token!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_superuser", False):
        print("🚫 [DEPENDS] User is logged in but is NOT a superuser!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Superuser access required.",
        )

    print("✅ [DEPENDS] Superuser authorized! Returning user dict.")
    return user


require_superuser = get_current_superuser
