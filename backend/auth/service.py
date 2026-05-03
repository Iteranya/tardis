from typing import Optional
from pocketbase import PocketBase
from backend.auth.manager import AuthManager
from backend.auth.schema import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    SetupInitializeRequest,
    SetupInitializeResponse,
    TestConnectionResponse,
    MeResponse,
    UserResponse,
)
from backend.util.secrets import get_secrets
import json  # Aina added this for pretty printing!


class AuthService:

    def __init__(self):
        self.manager = AuthManager()
        print("🤖 [SERVICE] Auth Service initialized!")

    # ─── Setup ───

    def test_connection(self, url: str) -> TestConnectionResponse:
        print("\n" + "=" * 60)
        print(f"🌐 [SERVICE test_connection] Testing URL: {url}")
        original_url = self.manager.pb_url
        self.manager.pb_url = url
        try:
            result = self.manager.test_connection()
            print(f"📦 [SERVICE test_connection] manager result: {result}")
            response = TestConnectionResponse(
                ok=result.get("ok", False),
                version=result.get("version"),
                message=result.get("message"),
            )
            print(f"✅ [SERVICE test_connection] Response created: ok={response.ok}")
            return response
        finally:
            self.manager.pb_url = original_url
            print(f"🔄 [SERVICE test_connection] Restored original URL")

    def initialize(self, data: SetupInitializeRequest) -> SetupInitializeResponse:
        print("\n" + "=" * 60)
        print("🚀 [SERVICE initialize] FULL SETUP INITIALIZATION TRIGGERED")
        print(f"📧 Admin email: {data.admin.email}")
        print(f"🌐 PB URL: {data.pocketbase.url}")
        print(f"🏠 Site name: {data.site.name}")

        self.manager.pb_url = data.pocketbase.url

        # Test connection
        connection = self.manager.test_connection()
        print(f"🔌 [SERVICE initialize] Connection test: {connection}")
        if not connection.get("ok"):
            return SetupInitializeResponse(
                ok=False,
                message=f"Cannot connect to PocketBase: {connection.get('message', 'Unknown error')}",
            )

        if self.manager.check_superuser_exists():
            print("👤 [SERVICE initialize] Superuser already exists!")
            return SetupInitializeResponse(
                ok=False,
                message="A superuser already exists! Please go to login page.",
            )
        print("✅ [SERVICE initialize] No superuser exists. Proceeding...")

        try:
            superuser = self.manager.create_superuser(
                data.admin.email,
                data.admin.password,
            )
            print(f"✅ [SERVICE initialize] Superuser created: {superuser.get('id', 'NO ID')}")
        except PermissionError as e:
            print(f"❌ [SERVICE initialize] PermissionError: {e}")
            return SetupInitializeResponse(ok=False, message=str(e))
        except Exception as e:
            print(f"❌ [SERVICE initialize] Unexpected create error: {e}")
            return SetupInitializeResponse(ok=False, message=f"Failed to create superuser: {str(e)}")

        # Login to get a token
        try:
            auth_data = self.manager.login_superuser(data.admin.email, data.admin.password)
            print(f"🔑 [SERVICE initialize] Login success! Token pref: {str(auth_data.get('token'))[:20]}...")
        except Exception as e:
            print(f"❌ [SERVICE initialize] Login failed after creation: {e}")
            return SetupInitializeResponse(ok=False, message=f"Failed to authenticate: {str(e)}")

        token = auth_data.get("token", "")
        user = auth_data.get("record", superuser)
        print(f"👤 [SERVICE initialize] User from auth: {json.dumps(user, default=str, indent=2)}")

        # Initialize collections
        try:
            self._initialize_collections(token)
        except Exception as e:
            print(f"⚠️ [SERVICE initialize] Collection initialization warning: {e}")

        # Create initial site page
        try:
            self._create_initial_site(token, data.site.name, data.site.url)
        except Exception as e:
            print(f"⚠️ [SERVICE initialize] Site creation warning: {e}")

        # Save credentials
        secrets = get_secrets()
        secrets.set("pocketbase.url", data.pocketbase.url, save=False)
        secrets.set("pocketbase.admin_email", data.admin.email, save=False)
        secrets.set("pocketbase.admin_password", data.admin.password, save=True)
        print("💾 [SERVICE initialize] Credentials saved to secrets.json!")

        print("✅ [SERVICE initialize] Setup complete! Returning success response.")
        return SetupInitializeResponse(
            ok=True,
            token=token,
            user={"id": user.get("id", ""), "email": user.get("email", ""), "is_superuser": True},
            message="Anita-CMS has been initialized successfully!",
        )

    def _initialize_collections(self, token: str) -> None:
        print("\n----- [SERVICE _initialize_collections] -----")
        print(f"🔑 Token pref: {token[:20]}...")
        from backend.pages.service import PageService
        from backend.articles.service import ArticleService
        from backend.sites.service import SiteService
        from backend.collections.service import CollectionService
        from backend.storage.service import StorageService
        from backend.users.service import UserService

        services = [
            ("Pages", PageService()),
            ("Articles", ArticleService()),
            ("Sites", SiteService()),
            ("Collections", CollectionService()),
            ("Storage", StorageService()),
            ("Users", UserService()),
        ]

        for name, service in services:
            try:
                service.initialize()
                print(f"  ✅ [SERVICE] {name} collection initialized")
            except Exception as e:
                print(f"  ⚠️ [SERVICE] {name} initialization skipped: {e}")

    def _create_initial_site(self, token: str, site_name: str, site_url: str) -> None:
        print("\n----- [SERVICE _create_initial_site] -----")
        print(f"🏠 Creating site: {site_name} at {site_url}")
        client = PocketBase(self.manager.pb_url)
        client.auth_store.save(token)
        print(f"🔑 Token saved to SDK session")

        try:
            existing = client.collection("pages").get_list(
                perPage=1,
                filter='slug = "home"',
            )
            print(f"🔍 Existing home pages: {existing.total_items}")
            if existing.total_items > 0:
                print("✅ Home page already exists, skipping.")
                return
        except Exception as e:
            print(f"⚠️ Check for existing home failed (probably fine): {e}")

        try:
            print("🆕 Creating home page...")
            result = client.collection("pages").create({
                "title": "Home",
                "slug": "home",
                "desc": f"Welcome to {site_name}!",
                "enabled": True,
                "sort_order": 0,
                "custom": {
                    "site_name": site_name,
                    "site_url": site_url,
                },
            })
            print(f"✅ Home page created! ID: {result.id if hasattr(result, 'id') else 'NO ID'}")
        except Exception as e:
            print(f"⚠️ Home page creation failed: {e}")

    # ─── Login ───

    def login(self, data: LoginRequest) -> Optional[LoginResponse]:
        print("\n" + "=" * 60)
        print("💥 [SERVICE login] FIRED!")
        print(f"📧 Email/Username: {data.email}")
        print(f"🔑 Password provided: {'YES' if data.password else 'NO'}")
        print(f"🫂 Remember me: {data.remember}")

        # ── Try Superuser ──
        try:
            print("[SERVICE login] Attempting superuser login...")
            auth_data = self.manager.login_superuser(data.email, data.password)
            print("✅ [SERVICE login] Superuser login successful!")
            print(f"📦 Raw auth_data type: {type(auth_data)}")
            print(f"📦 Raw auth_data keys: {auth_data.keys() if isinstance(auth_data, dict) else 'NOT A DICT!'}")

            if isinstance(auth_data, dict):
                token_raw = auth_data.get("token", "")
                record_raw = auth_data.get("record", {})
                print(f"🐍 Record type: {type(record_raw)}")
                print(f"🐍 Record has model_dump: {hasattr(record_raw, 'model_dump')}")
                print(f"🐍 Record has dict: {hasattr(record_raw, '__dict__')}")

                # FORCE record to a plain dict!
                if hasattr(record_raw, 'model_dump'):
                    record_dict = record_raw.model_dump()
                elif hasattr(record_raw, '__dict__'):
                    record_dict = dict(record_raw.__dict__)
                else:
                    record_dict = dict(record_raw)

                print(f"📦 Converted record dict: {record_dict}")

                response = LoginResponse(
                    token=str(token_raw),
                    user=record_dict,
                    is_superuser=True,
                )
                print(f"✅ [SERVICE login] LoginResponse created! Token: {response.token[:20]}...")
                print(f"✅ [SERVICE login] User keys: {response.user.keys()}")
            else:
                print("❌ auth_data is not a dict! It's: {type(auth_data)}")
                return None

            return response

        except Exception as e:
            print(f"❌ [SERVICE login] Superuser login error: {e}")
            import traceback
            traceback.print_exc()
            print("➡️ Falling through to regular user login...")

        # ── Try Regular User ──
        try:
            print("[SERVICE login] Attempting regular user login...")
            auth_data = self.manager.login_user(data.email, data.password)
            print("✅ [SERVICE login] Regular user login successful!")
            print(f"📦 Raw auth_data: {auth_data}")

            record_raw = auth_data.get("record", {})
            if hasattr(record_raw, 'model_dump'):
                record_dict = record_raw.model_dump()
            elif hasattr(record_raw, '__dict__'):
                record_dict = dict(record_raw.__dict__)
            else:
                record_dict = dict(record_raw)

            response = LoginResponse(
                token=str(auth_data.get("token", "")),
                user=record_dict,
                is_superuser=False,
            )
            print(f"✅ [SERVICE login] User LoginResponse created!")
            return response

        except Exception as e:
            print(f"❌ [SERVICE login] Regular user login error: {e}")
            import traceback
            traceback.print_exc()

        print("💀 [SERVICE login] NO AUTH METHOD WORKED. Returning None.")
        return None

    # ─── Register ───

    def register(self, data: RegisterRequest) -> Optional[RegisterResponse]:
        print("\n" + "=" * 60)
        print("📝 [SERVICE register] FIRED!")
        print(f"👤 Username: {data.username}")
        print(f"📧 Email: {data.email}")
        print(f"🔐 Passwords match: {data.password == data.passwordConfirm}")

        if data.password != data.passwordConfirm:
            print("❌ [SERVICE register] Passwords do not match!")
            raise ValueError("Passwords do not match!")

        try:
            print("[SERVICE register] Calling manager.register_user...")
            reg_result = self.manager.register_user(data.username, data.email, data.password)
            print(f"✅ [SERVICE register] Registration result: {reg_result}")

            # Auto-login
            print("[SERVICE register] Auto-logging in...")
            auth_data = self.manager.login_user(data.email, data.password)
            print(f"✅ [SERVICE register] Auto-login result: {auth_data}")

            record_raw = auth_data.get("record", reg_result.get("record"))
            if hasattr(record_raw, 'model_dump'):
                record_dict = record_raw.model_dump()
            elif hasattr(record_raw, '__dict__'):
                record_dict = dict(record_raw.__dict__)
            else:
                record_dict = dict(record_raw)

            response = RegisterResponse(
                token=str(auth_data.get("token", "")),
                user=record_dict,
            )
            print(f"✅ [SERVICE register] RegisterResponse created!")
            return response

        except Exception as e:
            print(f"❌ [SERVICE register] Error: {e}")
            try:
                message = e.message if hasattr(e, 'message') else str(e)
            except:
                message = str(e)
            print(f"📄 Extracted message: {message}")
            raise ValueError(message)

    # ─── Me ───

    def get_me(self, token: str) -> Optional[MeResponse]:
        print("\n" + "=" * 60)
        print("👤 [SERVICE get_me] FIRED!")
        print(f"🔑 Token: {token[:50]}...")

        user = self.manager.get_user_by_token(token)
        print(f"📦 [SERVICE get_me] Manager returned: {user}")

        if not user:
            print("🚫 [SERVICE get_me] No user found for token!")
            return None

        print(f"👤 User dict: {user}")
        print(f"🔑 is_superuser: {user.get('is_superuser', 'KEY NOT FOUND')}")
        print(f"🆔 ID: {user.get('id', 'KEY NOT FOUND')}")
        print(f"📧 Email: {user.get('email', 'KEY NOT FOUND')}")
        print(f"👤 Username: {user.get('username', 'KEY NOT FOUND')}")
        print(f"✅ Verified: {user.get('verified', 'KEY NOT FOUND')}")
        print(f"🖼 Avatar: {user.get('avatar', 'KEY NOT FOUND')}")
        print(f"📅 Created: {user.get('created', 'KEY NOT FOUND')}")
        print(f"🔄 Updated: {user.get('updated', 'KEY NOT FOUND')}")

        # Try building the UserResponse to catch Pydantic errors
        try:
            user_resp = UserResponse(
                id=user.get("id", ""),
                email=user.get("email", ""),
                username=user.get("username"),
                verified=user.get("verified", False),
                avatar=user.get("avatar"),
                created=user.get("created", ""),
                updated=user.get("updated", ""),
            )
            print(f"✅ [SERVICE get_me] UserResponse created successfully!")
        except Exception as e:
            print(f"❌ [SERVICE get_me] FAILED TO CREATE UserResponse: {e}")
            # Check each field individually
            for k in ["id", "email", "username", "verified", "avatar", "created", "updated"]:
                v = user.get(k)
                print(f"   '{k}' = {v} (type: {type(v).__name__})")
            raise

        try:
            me_resp = MeResponse(user=user_resp, is_superuser=user.get("is_superuser", False))
            print(f"✅ [SERVICE get_me] MeResponse created!")
            print(f"📦 MeResponse dump: {me_resp.model_dump()}")
            return me_resp
        except Exception as e:
            print(f"❌ [SERVICE get_me] FAILED TO CREATE MeResponse: {e}")
            raise
