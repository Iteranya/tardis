from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from backend.auth.service import AuthService
from backend.auth.schema import (
    LoginRequest, LoginResponse,
    RegisterRequest, RegisterResponse,
    SaveCredentialsRequest,
    TestConnectionRequest, TestConnectionResponse,
    MeResponse,
    ValidateCredentialsRequest,
)
from backend.util.initializer import initialize_all_modules
from backend.util.secrets import SecretsManager


templates = Jinja2Templates(directory="frontend")


def _setup_required() -> bool:
    secrets = SecretsManager()
    if not secrets.is_configured:
        print("🔴 [ROUTER _setup_required] Secrets not configured!")
        return True
    if not secrets.get("initialized", False):
        print("🔴 [ROUTER _setup_required] Not initialized!")
        return True
    print("🟢 [ROUTER _setup_required] Setup not required.")
    return False

def _maybe_redirect_to_setup(request: Request):
    if _setup_required():
        if not request.url.path.startswith("/auth/setup"):
            print("➡️ [ROUTER] Redirecting to /auth/setup")
            return RedirectResponse(url="/auth/setup")
    return None


api_router = APIRouter(prefix="/api", tags=["Auth API"])
page_router = APIRouter(prefix="/auth", tags=["Auth Pages"])


def get_service() -> AuthService:
    print("⚡ [ROUTER] Creating new AuthService instance!")
    return AuthService()


# ═══════════════════════════════════════════════
#  📄 PAGE ROUTES
# ═══════════════════════════════════════════════

@page_router.get("", response_class=HTMLResponse)
@page_router.get("/", response_class=HTMLResponse)
async def auth_index(request: Request):
    print("\n📄 [ROUTER] GET /auth")
    redirect = _maybe_redirect_to_setup(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("auth/login/login.html", {"request": request})


@page_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    print("\n📄 [ROUTER] GET /auth/login")
    redirect = _maybe_redirect_to_setup(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("auth/login/login.html", {"request": request})


@page_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    print("\n📄 [ROUTER] GET /auth/register")
    redirect = _maybe_redirect_to_setup(request)
    if redirect:
        return redirect
    return templates.TemplateResponse("auth/register/register.html", {"request": request})


@page_router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    print("\n📄 [ROUTER] GET /auth/setup")
    if not _setup_required():
        print("➡️ [ROUTER] Already configured, redirecting to login")
        return RedirectResponse(url="/auth/login")
    return templates.TemplateResponse("auth/setup/setup.html", {"request": request})


# ═══════════════════════════════════════════════
#  🔌 SETUP API ROUTES
# ═══════════════════════════════════════════════

@api_router.post("/setup/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    data: TestConnectionRequest,
    service: AuthService = Depends(get_service),
):
    print("\n🌐 [ROUTER] POST /api/setup/test-connection")
    print(f"   URL: {data.url}")
    return service.test_connection(data.url)


@api_router.post("/setup/validate-credentials")
async def validate_credentials(
    data: ValidateCredentialsRequest,
    service: AuthService = Depends(get_service),
):
    print("\n✅ [ROUTER] POST /api/setup/validate-credentials")
    print(f"   URL: {data.url}")
    print(f"   Email: {data.email}")
    print(f"   Password provided: {'YES' if data.password else 'NO'}")

    service.manager.pb_url = data.url

    try:
        auth_data = service.manager.login_superuser(data.email, data.password)
        print(f"✅ [ROUTER] Validation success! User ID: {auth_data.get('record', {}).get('id', 'NO ID')}")
        return {
            "ok": True,
            "message": "Credentials are valid!",
            "user": {
                "id": auth_data.get("record", {}).get("id", ""),
                "email": auth_data.get("record", {}).get("email", ""),
            },
        }
    except Exception as e:
        print(f"❌ [ROUTER] Validation failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid credentials: {str(e)}")


@api_router.post("/setup/save-credentials")
async def save_credentials(data: SaveCredentialsRequest):
    print("\n💾 [ROUTER] POST /api/setup/save-credentials")
    print(f"   URL: {data.url}")
    print(f"   Email: {data.email}")

    from backend.util.secrets import SecretsManager
    secrets = SecretsManager()
    secrets.set("pocketbase.url", data.url, save=False)
    secrets.set("pocketbase.admin_email", data.email, save=False)
    secrets.set("pocketbase.admin_password", data.password, save=True)
    print("✅ [ROUTER] Credentials saved!")
    return {"ok": True, "message": "Credentials saved to secrets.json."}


@api_router.post("/setup/initialize-collections")
async def initialize_collections():
    print("\n⚙️ [ROUTER] POST /api/setup/initialize-collections")
    print("  🔧 Running on-demand collection initialization...")
    results = initialize_all_modules()
    print(f"  📦 Results: {results}")
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
    print("\n" + "=" * 60)
    print("🌐 [ROUTER] POST /api/auth/login")
    print(f"📧 LoginRequest: email={data.email}, password_len={len(data.password)}, remember={data.remember}")

    result = service.login(data)

    print(f"📦 Result from service.login(): {result}")
    print(f"🐍 Type of result: {type(result)}")

    if isinstance(result, LoginResponse):
        print(f"✅ LoginResponse object created!")
        print(f"   token pref: {result.token[:20]}...")
        print(f"   is_superuser: {result.is_superuser}")
        print(f"   user keys: {result.user.keys() if hasattr(result.user, 'keys') else 'NOPE'}")

    if not result:
        print("🚫 Login failed (returned None or falsy)!")
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    print("💚 [ROUTER] Returning successful login response to client!")
    return result


@api_router.post("/auth/register", response_model=RegisterResponse)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_service),
):
    print("\n" + "=" * 60)
    print("🌐 [ROUTER] POST /api/auth/register")
    print(f"📧 Email: {data.email}")
    print(f"👤 Username: {data.username}")
    print(f"🔐 Password provided: {'YES' if data.password else 'NO'}")

    try:
        result = service.register(data)
        print(f"✅ [ROUTER] Registration successful! Token pref: {result.token[:20]}...")
        return result
    except ValueError as e:
        print(f"❌ [ROUTER] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ [ROUTER] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@api_router.get("/auth/me", response_model=MeResponse)
async def get_me(
    authorization: str = Header(None),
    service: AuthService = Depends(get_service),
):
    print("\n" + "=" * 60)
    print("🌐 [ROUTER] GET /api/auth/me")
    print(f"📩 Authorization header: {authorization}")

    if not authorization:
        print("🚫 No Authorization header present!")
        raise HTTPException(status_code=401, detail="Not authenticated.")

    token = authorization.replace("Bearer ", "").strip()
    print(f"🔑 Extracted token: {token[:50]}...")

    if not token:
        print("🚫 Token is empty after stripping!")
        raise HTTPException(status_code=401, detail="Invalid token.")

    result = service.get_me(token)
    print(f"📦 Service.get_me returned: {result}")

    if not result:
        print("🚫 Service returned None or falsy!")
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    # Test FastAPI response validation
    try:
        print("📝 [ROUTER] Testing MeResponse.response_model validation...")
        validated = MeResponse.model_validate(result)
        print(f"✅ [ROUTER] Validation passed! {validated.model_dump()}")
    except Exception as e:
        print(f"❌ [ROUTER] CRITICAL: Validation failed! {e}")
        raise HTTPException(
            status_code=500,
            detail="Server error: Response validation failed."
        )

    print("💚 [ROUTER] Returning MeResponse successfully!")
    return result


@api_router.post("/auth/logout")
async def logout():
    print("\n🚪 [ROUTER] POST /api/auth/logout")
    return {"ok": True, "message": "Logged out successfully."}
