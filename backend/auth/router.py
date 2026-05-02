from fastapi import APIRouter, HTTPException, Depends, Header
from backend.auth.service import AuthService
from backend.auth.schema import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    SetupInitializeRequest,
    SetupInitializeResponse,
    TestConnectionRequest,
    TestConnectionResponse,
    MeResponse,
)


router = APIRouter(
    prefix="/api",
    tags=["Auth"],
)


def get_service() -> AuthService:
    return AuthService()


# ─── Setup Routes ───

@router.post("/setup/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    data: TestConnectionRequest,
    service: AuthService = Depends(get_service),
):
    """Test if a PocketBase URL is reachable."""
    return service.test_connection(data.url)


@router.post("/setup/initialize", response_model=SetupInitializeResponse)
async def initialize_system(
    data: SetupInitializeRequest,
    service: AuthService = Depends(get_service),
):
    """
    Initialize Anita-CMS for the first time.

    This will:
    1. Test the PocketBase connection
    2. Create the superadmin account
    3. Initialize all collections
    4. Create the initial site/home page
    """
    return service.initialize(data)


# ─── Auth Routes ───

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_service),
):
    """
    Authenticate a user.

    Tries superuser first, then regular user.
    """
    result = service.login(data)
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )
    return result


@router.post("/auth/register", response_model=RegisterResponse)
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


@router.get("/auth/me", response_model=MeResponse)
async def get_me(
    authorization: str = Header(None),
    service: AuthService = Depends(get_service),
):
    """Get the currently authenticated user's info."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token.")

    result = service.get_me(token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    return result


@router.post("/auth/logout")
async def logout():
    """
    Logout the current user.

    Note: PocketBase uses JWT tokens, so logout is handled
    client-side by removing the token. This endpoint exists
    for API completeness.
    """
    return {"ok": True, "message": "Logged out successfully."}
