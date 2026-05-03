from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException, Depends, Header
from backend.auth.service import AuthService
from backend.auth.schema import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    SaveCredentialsRequest,
    TestConnectionRequest,
    TestConnectionResponse,
    MeResponse,
    UserResponse,
    ValidateCredentialsRequest,
)
from backend.util.dependencies import AuthDependency
from backend.util.initializer import initialize_all_modules
from backend.util.secrets import SecretsManager


# ─── Template Setup ───
templates = Jinja2Templates(directory="frontend")


# ─── Helper: Check if setup is needed ───

def _setup_required() -> bool:
    secrets = SecretsManager()
    if not secrets.is_configured:
        return True
    if not secrets.get("initialized", False):
        return True
    return False

def _maybe_redirect_to_setup(request: Request):
    """Redirect to /auth/setup if system isn't configured yet."""
    if _setup_required():
        # Don't redirect if already on setup page
        if not request.url.path.startswith("/auth/setup"):
            return RedirectResponse(url="/auth/setup")
    return None


# ─── API Router ───
api_router = APIRouter(
    prefix="/api",
    tags=["Auth API"],
)


# ─── Page Router (serves HTML) ───
page_router = APIRouter(
    prefix="/auth",
    tags=["Auth Pages"],
)


def get_service() -> AuthService:
    return AuthService()


# ═══════════════════════════════════════════════
#  📄 PAGE ROUTES — Serve the HTML UI
# ═══════════════════════════════════════════════

@page_router.get("", response_class=HTMLResponse)
@page_router.get("/", response_class=HTMLResponse)
async def auth_index(request: Request):
    """Redirect to login or setup based on configuration."""
    # Check if setup is needed
    redirect = _maybe_redirect_to_setup(request)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        "auth/login/login.html",
        {"request": request},
    )


@page_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page. Redirects to setup if not configured."""
    redirect = _maybe_redirect_to_setup(request)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        "auth/login/login.html",
        {"request": request},
    )


@page_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render the register page. Redirects to setup if not configured."""
    redirect = _maybe_redirect_to_setup(request)
    if redirect:
        return redirect

    return templates.TemplateResponse(
        "auth/register/register.html",
        {"request": request},
    )


@page_router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """Render the setup wizard. Redirect if already configured."""
    if not _setup_required():
        # Already configured, send to login
        return RedirectResponse(url="/auth/login")

    return templates.TemplateResponse(
        "auth/setup/setup.html",
        {"request": request},
    )


# ═══════════════════════════════════════════════
#  🔌 SETUP API ROUTES — Each does ONE thing
# ═══════════════════════════════════════════════

@api_router.post("/setup/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    data: TestConnectionRequest,
    service: AuthService = Depends(get_service),
):
    """Test if a PocketBase URL is reachable."""
    return service.test_connection(data.url)


@api_router.post("/setup/validate-credentials")
async def validate_credentials(
    data: ValidateCredentialsRequest,
    service: AuthService = Depends(get_service),
):
    """Check if the provided credentials can log in to PocketBase.

    Does NOT save anything. Just validates.
    """
    service.manager.pb_url = data.url

    try:
        auth_data = service.manager.login_superuser(data.email, data.password)
        return {
            "ok": True,
            "message": "Credentials are valid!",
            "user": {
                "id": auth_data.get("record", {}).get("id", ""),
                "email": auth_data.get("record", {}).get("email", ""),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid credentials: {str(e)}",
        )


@api_router.post("/setup/save-credentials")
async def save_credentials(
    data: SaveCredentialsRequest,
):
    """Save PocketBase credentials to secrets.json. ONLY saves, nothing else."""
    from backend.util.secrets import SecretsManager
    secrets = SecretsManager()
    secrets.set("pocketbase.url", data.url, save=False)
    secrets.set("pocketbase.admin_email", data.email, save=False)
    secrets.set("pocketbase.admin_password", data.password, save=True)
    return {"ok": True, "message": "Credentials saved to secrets.json."}

@api_router.post("/setup/initialize-collections")
async def initialize_collections():
    """Initialize all system collections in PocketBase.

    Uses the same logic as startup init, but can be called
    on-demand from the setup wizard.
    """
    print("  🔧 Running on-demand collection initialization...")
    results = initialize_all_modules()

    all_ok = all(v == "✅" for v in results.values())
    return {
        "ok": all_ok,
        "results": results,
        "message": "All collections initialized!" if all_ok else "Some collections had issues.",
    }

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_service),
):
    """Authenticate a user."""
    result = service.login(data)
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )
    return result


@api_router.post("/auth/register", response_model=RegisterResponse)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_service),
):
    """Register a new user account."""
    try:
        return service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@api_router.get("/auth/me", response_model=MeResponse)
async def get_me(
    user = Depends(AuthDependency()),
):
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
        is_superuser=user.get("_collection") == "_superusers",
    )


@api_router.post("/auth/logout")
async def logout():
    """Logout the current user."""
    return {"ok": True, "message": "Logged out successfully."}


# ─── Export both routers ───
__all__ = ["api_router", "page_router"]
