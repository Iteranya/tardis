from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

# --- Service, Schema, and Auth Imports ---
from data.database import get_db
from data import schemas
from services.users import UserService, hash_password
from src.dependencies import get_current_user, require_admin
from data.schemas import CurrentUser

# --- Dependency Setup ---

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency provider for the UserService."""
    return UserService(db)

# --- Router Definition ---
router = APIRouter(prefix="/users", tags=["User & Role Management"])

# --- Pydantic Model for Password Resets ---
class PasswordReset(BaseModel):
    new_password: str

# ==========================================
# ROLE MANAGEMENT
# ==========================================

@router.get("/roles", response_model=List[schemas.Role]) 
def get_roles(
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """List all available roles."""
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this page."
        )
    
    # Get the Dict[str, List[str]] from service
    roles_dict = user_service.get_all_roles()
    
    # Convert Dict to List[Role Object] for the frontend
    return [
        schemas.Role(role_name=k, permissions=v) 
        for k, v in roles_dict.items()
    ]

@router.get("/role_name", response_model=List[str]) # Should be safe??? Eh, it's fine, too much paranoia isn't good for you.
def get_role_name(
    user_service: UserService = Depends(get_user_service),
    user: CurrentUser = Depends(get_current_user),
):
    """List all available role names."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this page."
        )
    
    roles_dict = user_service.get_all_roles()
    
    return list(roles_dict.keys())


@router.post("/roles", response_model=schemas.Role)
def create_or_update_role(
    role_data: schemas.RoleCreate,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """
    Create a new role or update permissions for an existing one.
    The service layer handles protection of the 'admin' role.
    """
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this page."
        )
    return user_service.save_role(role_data)

@router.delete("/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_name: str,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """
    Delete a role. The service layer protects core roles from deletion.
    """
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this page."
        )
    user_service.delete_role(role_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# USER MANAGEMENT
# ==========================================

@router.get("/", response_model=List[schemas.User])
def list_users(
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """Returns a list of all users. The password hash is automatically excluded by the Pydantic model."""
    return user_service.get_all_users()

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_new_user(
    new_user: schemas.UserCreateWithPassword,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """Admin-only endpoint to create a new user. The service handles validation. Public register exists in auth route"""
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this page."
        )
    
    return user_service.create_user(new_user)

@router.put("/{target_username}", response_model=schemas.User)
def update_user(
    target_username: str,
    update_data: schemas.UserUpdate,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """
    Update a user's details (role, display name, etc.).
    Note: This endpoint does NOT handle password changes.
    """
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this page."
        )
    return user_service.update_user(username=target_username, user_update=update_data)

@router.put("/{target_username}/password")
def change_user_password(
    target_username: str,
    password_data: PasswordReset,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """
    Admin-only endpoint to set a new password for any user.
    """
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this page."
        )
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    db_user = user_service.get_user_by_username(target_username)
    db_user.hashed_password = hash_password(password_data.new_password)
    user_service.db.commit()

    return {"message": f"Password for user '{target_username}' has been updated."}

@router.delete("/{target_username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    target_username: str,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """Deletes a user. You cannot delete your own account."""
    # Authorization: Prevent an admin from deleting their own account via the API.
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this page."
        )
    if target_username == admin.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account while logged in."
        )
        
    user_service.delete_user(target_username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ==========================================
# API KEY MANAGEMENT
# ==========================================

@router.post("/{target_username}/key", response_model=schemas.User)
def generate_user_api_key(
    target_username: str,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """
    Generate a new API key for a user.
    Returns the user object with the new key (key is included in response).
    """
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to generate API keys."
        )

    return user_service.regenerate_api_key(target_username)

@router.delete("/{target_username}/key", status_code=status.HTTP_204_NO_CONTENT)
def revoke_user_api_key(
    target_username: str,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """
    Revoke a user's API key by setting it to null.
    """
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to revoke API keys."
        )

    user = user_service.get_user_by_username(target_username)
    user.key = None

    user_service.db.add(user)
    user_service.db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{target_username}/key/verify")
def verify_api_key_status(
    target_username: str,
    user_service: UserService = Depends(get_user_service),
    admin: CurrentUser = Depends(require_admin),
):
    """
    Check if a user has an active API key (without revealing the key itself).
    Returns a boolean indicating key status.
    """
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to check API key status."
        )

    user = user_service.get_user_by_username(target_username)
    return {"has_api_key": user.key is not None}

# ==========================================
# SELF-SERVICE API KEY MANAGEMENT (for users to manage their own keys)
# ==========================================

@router.post("/me/key", response_model=schemas.CurrentUser)
def generate_my_api_key(
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate a new API key for the currently logged-in user.
    Returns the current user object with the new key.
    """
    user = user_service.regenerate_api_key(current_user.username)

    # Return a CurrentUser response with the new key
    return schemas.CurrentUser(
        username=user.username,
        role=user.role,
        display_name=user.display_name,
        key=user.key,  # Include the key in response for self-service
        exp=current_user.exp
    )

@router.delete("/me/key", status_code=status.HTTP_204_NO_CONTENT)
def revoke_my_api_key(
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Revoke your own API key.
    """
    user = user_service.get_user_by_username(current_user.username)
    user.key = None

    user_service.db.add(user)
    user_service.db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/me/key/status")
def check_my_api_key_status(
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Check if you have an active API key.
    Returns a boolean indicating key status.
    """
    user = user_service.get_user_by_username(current_user.username)
    return {"has_api_key": user.key is not None}
