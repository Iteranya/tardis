from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# ─── Setup ───

class TestConnectionRequest(BaseModel):
    url: str = Field(..., description="PocketBase server URL")


class TestConnectionResponse(BaseModel):
    ok: bool
    version: Optional[str] = None
    message: Optional[str] = None


class SetupAdminInfo(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class SetupSiteInfo(BaseModel):
    name: str
    url: str


class SetupInitializeRequest(BaseModel):
    pocketbase: TestConnectionRequest
    admin: SetupAdminInfo
    site: SetupSiteInfo


class SetupInitializeResponse(BaseModel):
    ok: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: Optional[str] = None


# ─── Login ───

class LoginRequest(BaseModel):
    email: str = Field(..., description="Email or username")
    password: str
    remember: bool = False


class LoginResponse(BaseModel):
    token: str
    user: dict
    is_superuser: bool = False


# ─── Register ───

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    passwordConfirm: str


class RegisterResponse(BaseModel):
    token: str
    user: dict


# ─── Me / User Info ───

class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    verified: bool = False
    avatar: Optional[str] = None
    created: str
    updated: str


class MeResponse(BaseModel):
    user: UserResponse
    is_superuser: bool = False
