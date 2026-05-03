from fastapi import Header, HTTPException
from typing import Optional
from backend.util.verification import VerifyIdentity


class AuthDependency:
    """
    Aina-chan's FastAPI dependency for verifying identity! (◕‿◕✿)

    Usage:
        @app.get("/profile")
        async def profile(user = Depends(AuthDependency())):
            return {"email": user["email"]}

        @app.get("/admin")
        async def admin(user = Depends(AuthDependency(require_superuser=True))):
            return {"email": user["email"], "role": "superuser"}
    """

    def __init__(self, require_superuser: bool = False):
        self.require_superuser = require_superuser
        self.verifier = VerifyIdentity()

    async def __call__(self, authorization: Optional[str] = Header(None)):
        # 1️⃣ Check header exists
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Aina-chan needs an Authorization header! (╥﹏╥)",
            )

        # 2️⃣ Parse "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization format. Use: Bearer <token>",
            )

        token = parts[1]

        # 3️⃣ Verify the token via VerifyIdentity
        user = self.verifier.verify_token(token)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Token is invalid or expired! (╥﹏╥)",
            )

        # 4️⃣ Optionally require superuser
        if self.require_superuser and user.get("_collection") != "_superusers":
            raise HTTPException(
                status_code=403,
                detail="This endpoint requires superuser privileges! (｀⌒´)",
            )

        return user
