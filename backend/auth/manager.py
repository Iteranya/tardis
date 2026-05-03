import os
from typing import Optional
from pocketbase import PocketBase
from backend.util.secrets import SecretsManager
import traceback  # Already imported in one method, but let's make it global


class AuthManager:

    def __init__(self, pb_url: Optional[str] = None):
        print("\n" + "=" * 60)
        print("🛠️ [AUTH MANAGER] __init__ CALLED")
        self._secrets = SecretsManager()
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
        print("\n" + "=" * 60)
        print("🔍 [get_user_by_token] CALLED")
        print(f"   Token length: {len(token)}")
        print(f"   Token[:50]: {token[:50]}...")
        print(f"   pb_url: {self.pb_url}")

        # ── TRY SUPERUSER REFRESH ──
        try:
            print("\n--- Attempting superuser auth_refresh ---")
            client = PocketBase(self.pb_url)
            print(f"   Client created. Saving token to auth store...")
            client.auth_store.save(token)
            print(f"   Token saved. Calling _superusers auth_refresh...")
            result = client.collection("_superusers").auth_refresh()
            print(f"   ✅ auth_refresh SUCCEEDED for superuser!")
            print(f"   Result type: {type(result)}")
            print(f"   Result has record? {hasattr(result, 'record')}")
            record = result.record
            print(f"   Record type: {type(record)}")

            # Print all attributes of record to see exact field names!
            print("   Record attributes & values:")
            for attr in dir(record):
                if not attr.startswith('_'):
                    val = getattr(record, attr)
                    print(f"      {attr}: {val!r} (type: {type(val).__name__})")

            # Build dict with explicit field names as expected by schema
            data = {
                "id": record.id,
                "email": record.email,
                # Use both possible attribute names and print them
                "emailVisibility": getattr(record, 'emailVisibility', None),
                "email_visibility": getattr(record, 'email_visibility', None),
                "username": getattr(record, 'username', None),
                "verified": getattr(record, 'verified', False),
                "avatar": getattr(record, 'avatar', None),
                "collectionId": record.collection_id,
                "collectionName": record.collection_name,
                "created": str(record.created) if record.created else None,
                "updated": str(record.updated) if record.updated else None,
            }
            print(f"   Built data dict for superuser:")
            for k, v in data.items():
                print(f"      {k}: {v!r} (type: {type(v).__name__})")
            data["is_superuser"] = True
            print(f"   Set is_superuser = True")
            return data

        except Exception as e:
            print(f"   ❌ Superuser auth_refresh failed!")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   Exception args: {e.args}")
            traceback.print_exc()
            if hasattr(e, 'response'):
                print(f"   Response status: {e.response.status_code}")
                print(f"   Response body: {e.response.text}")
            else:
                # Try to get the raw response from the client's last request?
                print("   No response attribute on exception.")

        # ── TRY REGULAR USER REFRESH ──
        try:
            print("\n--- Attempting regular user auth_refresh ---")
            client = PocketBase(self.pb_url)
            client.auth_store.save(token)
            print("   Calling users auth_refresh...")
            result = client.collection("users").auth_refresh()
            print(f"   ✅ auth_refresh SUCCEEDED for regular user!")
            record = result.record
            print(f"   Record type: {type(record)}")
            print("   Record attributes:")
            for attr in dir(record):
                if not attr.startswith('_'):
                    val = getattr(record, attr)
                    print(f"      {attr}: {val!r} (type: {type(val).__name__})")

            data = {
                "id": record.id,
                "email": record.email,
                "emailVisibility": getattr(record, 'emailVisibility', None),
                "email_visibility": getattr(record, 'email_visibility', None),
                "username": getattr(record, 'username', None),
                "verified": getattr(record, 'verified', False),
                "avatar": getattr(record, 'avatar', None),
                "collectionId": record.collection_id,
                "collectionName": record.collection_name,
                "created": str(record.created) if record.created else None,
                "updated": str(record.updated) if record.updated else None,
            }
            data["is_superuser"] = False
            print(f"   Built data dict for regular user:")
            for k, v in data.items():
                print(f"      {k}: {v!r}")
            return data

        except Exception as e:
            print(f"   ❌ Regular user auth_refresh also failed!")
            print(f"   Exception: {e}")
            traceback.print_exc()
            if hasattr(e, 'response'):
                print(f"   Response status: {e.response.status_code}")
                print(f"   Response body: {e.response.text}")

        print("   💀 Both auth methods failed. Returning None.")
        return None

    def refresh_token(self, token: str) -> Optional[dict]:
        print("\n===== 🔄 [refresh_token] =====")
        print(f"   Token[:20]: {token[:20]}...")

        # Try superuser
        try:
            print("   Trying superuser refresh...")
            client = self._client(token)
            result = client.collection("_superusers").auth_refresh()
            print(f"   ✅ Superuser refresh succeeded!")
            print(f"   New token[:20]: {result.token[:20]}...")
            return {"token": result.token, "record": result.record}
        except Exception as e:
            print(f"   ❌ Superuser refresh failed: {e}")
            traceback.print_exc()

        # Try regular user
        try:
            print("   Trying regular user refresh...")
            client = self._client(token)
            result = client.collection("users").auth_refresh()
            print(f"   ✅ Regular user refresh succeeded!")
            print(f"   New token[:20]: {result.token[:20]}...")
            return {"token": result.token, "record": result.record}
        except Exception as e:
            print(f"   ❌ Regular user refresh failed: {e}")
            traceback.print_exc()

        print("   💀 Both refresh attempts failed. Returning None.")
        return None
