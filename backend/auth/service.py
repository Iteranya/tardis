from typing import Optional
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


class AuthService:
    """
    Aina-chan's Auth Service! (◕‿◕✿)

    Business logic layer for authentication and setup.
    """

    def __init__(self):
        self.manager = AuthManager()

    # ─── Setup ───

    def test_connection(self, url: str) -> TestConnectionResponse:
        """Test if PocketBase is reachable."""
        # Temporarily override the URL for testing
        original_url = self.manager.pb_url
        self.manager.pb_url = url
        try:
            result = self.manager.test_connection()
            return TestConnectionResponse(
                ok=result.get("ok", False),
                version=result.get("version"),
                message=result.get("message"),
            )
        finally:
            self.manager.pb_url = original_url

    def initialize(self, data: SetupInitializeRequest) -> SetupInitializeResponse:
        """
        Full system initialization:
        1. Test connection
        2. Create superuser
        3. Initialize collections
        4. Create initial site
        """
        # Step 1: Set the PocketBase URL
        self.manager.pb_url = data.pocketbase.url

        # Step 2: Test connection
        connection = self.manager.test_connection()
        if not connection.get("ok"):
            return SetupInitializeResponse(
                ok=False,
                message=f"Cannot connect to PocketBase: {connection.get('message', 'Unknown error')}",
            )

        # Step 3: Check if superuser already exists
        if self.manager.check_superuser_exists():
            return SetupInitializeResponse(
                ok=False,
                message="A superuser already exists! Please go to login page.",
            )

        # Step 4: Create superuser
        try:
            superuser = self.manager.create_superuser(
                data.admin.email,
                data.admin.password,
            )
        except PermissionError as e:
            return SetupInitializeResponse(ok=False, message=str(e))
        except Exception as e:
            return SetupInitializeResponse(
                ok=False,
                message=f"Failed to create superuser: {str(e)}",
            )

        # Step 5: Login as superuser to get a token
        try:
            auth_data = self.manager.login_superuser(
                data.admin.email,
                data.admin.password,
            )
        except Exception as e:
            return SetupInitializeResponse(
                ok=False,
                message=f"Failed to authenticate: {str(e)}",
            )

        token = auth_data.get("token", "")
        user = auth_data.get("record", superuser)

        # Step 6: Initialize all collections
        try:
            self._initialize_collections(token)
        except Exception as e:
            # Non-fatal — collections can be created later
            print(f"⚠️ Collection initialization warning: {e}")

        # Step 7: Create initial site page (optional, non-fatal)
        try:
            self._create_initial_site(token, data.site.name, data.site.url)
        except Exception as e:
            print(f"⚠️ Site creation warning: {e}")

        # Save to secrets.json for persistence
        from backend.util.secrets import SecretsManager
        secrets = SecretsManager()
        secrets.set("pocketbase.url", data.pocketbase.url, save=False)
        secrets.set("pocketbase.admin_email", data.admin.email, save=False)
        secrets.set("pocketbase.admin_password", data.admin.password, save=True)

        return SetupInitializeResponse(
            ok=True,
            token=token,
            user={"id": user.get("id", ""), "email": user.get("email", ""), "is_superuser": True},
            message="Anita-CMS has been initialized successfully!",
        )

    def _initialize_collections(self, token: str) -> None:
        """Initialize all system collections."""
        # Import here to avoid circular imports during module loading
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
                print(f"  ✅ {name} collection initialized")
            except Exception as e:
                print(f"  ⚠️ {name} initialization skipped: {e}")

    def _create_initial_site(self, token: str, site_name: str, site_url: str) -> None:
        """Create an initial home page for the site."""
        import httpx

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Check if a home page already exists
        response = httpx.get(
            f"{self.manager.pb_url}/api/collections/pages/records",
            headers=headers,
            params={"filter": 'slug = "home"', "perPage": 1},
        )
        if response.ok:
            data = response.json()
            if data.get("totalItems", 0) > 0:
                return  # Home page already exists

        # Create home page
        httpx.post(
            f"{self.manager.pb_url}/api/collections/pages/records",
            headers=headers,
            json={
                "title": "Home",
                "slug": "home",
                "desc": f"Welcome to {site_name}!",
                "enabled": True,
                "sort_order": 0,
                "custom": {
                    "site_name": site_name,
                    "site_url": site_url,
                },
            },
            timeout=10,
        )

    # ─── Login ───

    def login(self, data: LoginRequest) -> Optional[LoginResponse]:
        """Try to authenticate a user. Checks superuser first, then regular user."""
        # Try superuser first
        try:
            auth_data = self.manager.login_superuser(data.email, data.password)
            return LoginResponse(
                token=auth_data.get("token", ""),
                user=auth_data.get("record", {}),
                is_superuser=True,
            )
        except Exception:
            pass

        # Try regular user
        try:
            auth_data = self.manager.login_user(data.email, data.password)
            return LoginResponse(
                token=auth_data.get("token", ""),
                user=auth_data.get("record", {}),
                is_superuser=False,
            )
        except Exception:
            pass

        return None

    # ─── Register ───

    def register(self, data: RegisterRequest) -> Optional[RegisterResponse]:
        """Register a new user."""
        if data.password != data.passwordConfirm:
            raise ValueError("Passwords do not match!")

        try:
            result = self.manager.register_user(data.username, data.email, data.password)
            # Auto-login after registration
            auth_data = self.manager.login_user(data.email, data.password)
            return RegisterResponse(
                token=auth_data.get("token", ""),
                user=auth_data.get("record", result),
            )
        except Exception as e:
            error_data = getattr(e, 'response', None)
            if error_data is not None:
                try:
                    err_json = error_data.json()
                    message = err_json.get("message", str(e))
                except Exception:
                    message = str(e)
            else:
                message = str(e)
            raise ValueError(message)

    # ─── Me ───

    def get_me(self, token: str) -> Optional[MeResponse]:
        """Get current user info from token."""
        user = self.manager.get_user_by_token(token)
        if not user:
            return None

        return MeResponse(
            user=UserResponse(
                id=user.get("id", ""),
                email=user.get("email", ""),
                username=user.get("username"),
                verified=user.get("verified", False),
                avatar=user.get("avatar"),
                created=user.get("created", ""),
                updated=user.get("updated", ""),
            ),
            is_superuser=user.get("is_superuser", False),
        )
