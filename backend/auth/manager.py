import time
from typing import Optional
import jwt
from pocketbase import PocketBase
from backend.util.secrets import get_secrets
import traceback  # Already imported in one method, but let's make it global


class AuthManager:

    def __init__(self, pb_url: Optional[str] = None):
        print("\n" + "=" * 60)
        print("🛠️ [AUTH MANAGER] __init__ CALLED")
        self._secrets = get_secrets()
        print(f"📂 SecretsManager created. Type: {type(self._secrets)}")
        print(f"🔑 SecretsManager has 'pocketbase_url'? {hasattr(self._secrets, 'pocketbase_url')}")
        if hasattr(self._secrets, 'pocketbase_url'):
            print(f"   Value from secrets: {self._secrets.pocketbase_url}")

        self.pb_url = pb_url or self._secrets.pocketbase_url
        print(f"🌐 Final pb_url: {self.pb_url}")
        print("🛠️ [AUTH MANAGER] __init__ COMPLETE")

    # ─── Create a fresh client for stateless operations ───

    def _client(self, token: Optional[str] = None) -> PocketBase:
        print(f"\n----- 🔧 [_client] creating PocketBase client -----")
        print(f"   pb_url: {self.pb_url}")
        print(f"   token provided: {'YES' if token else 'NO'}")
        if token:
            print(f"   token[:20]: {token[:20]}...")

        client = PocketBase(self.pb_url)
        print(f"   PocketBase instance created. Type: {type(client)}")

        if token:
            client.auth_store.save(token)
            print(f"   Token saved to auth_store.")
            # Optional: verify the token is retrievable
            print(f"   Auth store has token? {bool(client.auth_store.token)}")

        print(f"----- 🔧 [_client] returning client -----")
        return client

    # ─── Connection ───

    def test_connection(self) -> dict:
        print("\n===== 🌐 [test_connection] =====")
        print(f"   pb_url: {self.pb_url}")

        try:
            client = self._client()
            print("   Client created. Attempting collections.get_list(perPage=1)...")
            result = client.collections.get_list(perPage=1)
            print(f"   collections.get_list succeeded! Result: type={type(result)}")
            print(f"   Result has total_items? {hasattr(result, 'total_items')}")
            if hasattr(result, 'total_items'):
                print(f"   total_items: {result.total_items}")

            # Try to get version from settings
            print("   Attempting to get settings via client...")
            try:
                # The SDK may have a settings() method or we can try a different approach
                # Let's see what's available on the client object
                print(f"   Client methods (non-underscore): {[m for m in dir(client) if not m.startswith('_')]}")
                # For now, just return ok
                print("   Returning {'ok': True, 'version': 'unknown'}")
                print("===== 🌐 test_connection SUCCESS =====")
                return {"ok": True, "version": "unknown"}
            except Exception as verr:
                print(f"   Version fetch failed: {verr}")
                print("   Falling back to {'ok': True, 'version': 'unknown'}")
                return {"ok": True, "version": "unknown"}

        except Exception as e:
            print(f"   ❌ Connection test failed!")
            print(f"   Exception type: {type(e).__name__}")
            traceback.print_exc()
            msg = str(e)
            print(f"   Message: {msg}")
            if "ConnectError" in msg or "Timeout" in msg:
                print("   Reason: Cannot connect to PocketBase (ConnectError/Timeout)")
                return {"ok": False, "version": None, "message": "Cannot connect to PocketBase."}
            print("   Reason: General error")
            return {"ok": False, "version": None, "message": msg}

    def check_superuser_exists(self) -> bool:
        print("\n===== 🔍 [check_superuser_exists] =====")
        try:
            client = self._client()
            print("   Client created. Querying _superusers collection...")
            result = client.collection("_superusers").get_list(perPage=1)
            print(f"   Query result type: {type(result)}")
            print(f"   total_items: {result.total_items}")
            exists = result.total_items > 0
            print(f"   Superuser exists? {exists}")
            return exists
        except Exception as e:
            print(f"   ❌ Exception during check: {e}")
            traceback.print_exc()
            print("   Returning False (assuming no superuser exists)")
            return False

    # ─── Superuser Management ───

    def login_superuser(self, email: str, password: str) -> dict:
        print("\n===== 🔐 [login_superuser] =====")
        print(f"   Email: {email}")
        print(f"   Password length: {len(password)}")
        print(f"   pb_url: {self.pb_url}")

        client = self._client()
        print("   Client created. Calling auth_with_password...")
        try:
            result = client.collection("_superusers").auth_with_password(email, password)
            print(f"   auth_with_password succeeded!")
            print(f"   Result type: {type(result)}")
            print(f"   Result has token? {hasattr(result, 'token')}")
            if hasattr(result, 'token'):
                print(f"   token[:20]: {result.token[:20]}...")
            print(f"   Result has record? {hasattr(result, 'record')}")
            if hasattr(result, 'record'):
                print(f"   Record type: {type(result.record)}")
                print(f"   Record id: {getattr(result.record, 'id', 'NO ID')}")
                print(f"   Record email: {getattr(result.record, 'email', 'NO EMAIL')}")

            return {
                "token": result.token,
                "record": result.record,
            }
        except Exception as e:
            print(f"   ❌ login_superuser failed!")
            print(f"   Exception: {e}")
            traceback.print_exc()
            raise  # Re-raise after debug

    # ─── Regular User Management ───

    def login_user(self, email: str, password: str) -> dict:
        print("\n===== 🔐 [login_user] =====")
        print(f"   Email: {email}")
        print(f"   Password length: {len(password)}")

        client = self._client()
        print("   Client created. Calling users auth_with_password...")
        try:
            result = client.collection("users").auth_with_password(email, password)
            print(f"   Result type: {type(result)}")
            print(f"   token[:20]: {result.token[:20]}...")
            print(f"   Record type: {type(result.record)}")
            print(f"   Record id: {getattr(result.record, 'id', 'NO ID')}")

            return {
                "token": result.token,
                "record": result.record,
            }
        except Exception as e:
            print(f"   ❌ login_user failed: {e}")
            traceback.print_exc()
            raise

    def register_user(self, username: str, email: str, password: str) -> dict:
        print("\n===== 📝 [register_user] =====")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password length: {len(password)}")
        print(f"   PasswordConfirm: (same as password)")

        client = self._client()
        data = {
            "username": username,
            "email": email,
            "password": password,
            "passwordConfirm": password,
        }
        print(f"   Data to create: {data}")
        try:
            record = client.collection("users").create(data)
            print(f"   User created! Record type: {type(record)}")
            print(f"   Record id: {getattr(record, 'id', 'NO ID')}")
            print(f"   Record keys (if dict): {record if isinstance(record, dict) else 'not a dict'}")
            if not isinstance(record, dict):
                print(f"   Record attributes: {[a for a in dir(record) if not a.startswith('_')]}")
            return {"record": record}
        except Exception as e:
            print(f"   ❌ register_user failed: {e}")
            traceback.print_exc()
            raise

    # ─── Token Validation & Refresh ───

    def get_user_by_token(self, token: str) -> Optional[dict]:
        # 1. Decode JWT to get id
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("id")
            if not user_id:
                print("   ❌ No id in token")
                return None
            # Check expiry
            if time.time() > payload.get("exp", 0):
                print("   ❌ Token expired")
                return None
        except Exception as e:
            print(f"   ❌ JWT decode failed: {e}")
            return None

        # 3. Fetch record from PocketBase (no auth_refresh!)
        data = self._fetch_user_record(token, user_id)
        return data

    def _fetch_user_record(self, token: str, user_id: str) -> Optional[dict]:
        """Try to get the user record by ID using GET, not auth_refresh."""
        client = PocketBase(self.pb_url)
        client.auth_store.save(token)

        # Try superusers first
        try:
            print("   📡 Fetching from _superusers by ID...")
            record = client.collection("_superusers").get_one(user_id)
            print(f"   ✅ Found in _superusers")
            return {
                "id": record.id,
                "email": record.email,
                "username": getattr(record, 'username', None),
                "verified": getattr(record, 'verified', False),
                "avatar": getattr(record, 'avatar', None),
                "collectionId": record.collection_id,
                "collectionName": "_superusers",
                "created": str(record.created) if record.created else "",
                "updated": str(record.updated) if record.updated else "",
                "is_superuser": True,
            }
        except Exception as e:
            print(f"   ❌ Not in superusers: {e}")

        # Try regular users
        try:
            print("   📡 Fetching from users by ID...")
            record = client.collection("users").get_one(user_id)
            print(f"   ✅ Found in users")
            return {
                "id": record.id,
                "email": record.email,
                "username": getattr(record, 'username', None),
                "verified": getattr(record, 'verified', False),
                "avatar": getattr(record, 'avatar', None),
                "collectionId": record.collection_id,
                "collectionName": "users",
                "created": str(record.created) if record.created else "",
                "updated": str(record.updated) if record.updated else "",
                "is_superuser": False,
            }
        except Exception as e:
            print(f"   ❌ Not in users either: {e}")

        return None