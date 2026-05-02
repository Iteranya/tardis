"""
Anita-CMS Main Entry Point 🎀

A modular CMS built with FastAPI + PocketBase.
Each module is fully self-contained and can be deleted independently!
"""
import os
import getpass
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.util.secrets import SecretsManager


# ─── Import all modules ────────────────────────────────────────
# Each module is 100% independent!

from backend.pages.router import router as pages_router
from backend.articles.router import router as article_router
from backend.sites.router import router as site_router
from backend.collections.router import router as collections_router
from backend.storage.router import router as storage_router
from backend.users.router import router as users_router
from backend.auth.router import router as auth_router


# ─── Credential Setup ─────────────────────────────────────────

def _ensure_credentials():
    """
    Check if PocketBase credentials are configured.

    If not configured:
      - If --setup or SKIP_INIT=true → skip, web setup will handle it
      - Otherwise → prompt in terminal
    """
    secrets = SecretsManager()

    if secrets.is_configured:
        print("✅ PocketBase credentials found in secrets.json")
        return secrets

    # Check for skip flags
    skip_init = os.environ.get("SKIP_INIT", "").lower() in ("true", "1", "yes")
    web_setup = "--web-setup" in os.sys.argv or skip_init

    if web_setup:
        print("🌐 Web setup mode — credentials will be configured via browser")
        print("   Visit http://localhost:8000/auth/setup to get started!")
        return secrets

    # Terminal prompt (for local development)
    print("\n" + "=" * 50)
    print("  🔑  Aina-chan needs your PocketBase credentials!")
    print("  💡  Tip: Use --web-setup to set up via browser instead!")
    print("=" * 50)
    print("  (These will be saved to secrets.json for next time~)\n")

    # Prompt for PocketBase URL (optional, default is fine)
    default_url = secrets.pocketbase_url
    url_input = input(f"  🌐 PocketBase URL [{default_url}]: ").strip()
    if url_input:
        secrets.set("pocketbase.url", url_input, save=False)
    else:
        secrets.set("pocketbase.url", default_url, save=False)

    # Prompt for admin email (required)
    while True:
        email = input("  📧 Admin email: ").strip()
        if email:
            secrets.set("pocketbase.admin_email", email, save=False)
            break
        print("  ❌ Aina-chan needs an email to proceed! (╥﹏╥)")

    # Prompt for admin password (required, hidden input)
    while True:
        password = getpass.getpass("  🔒 Admin password: ").strip()
        if password:
            secrets.set("pocketbase.admin_password", password, save=False)
            break
        print("  ❌ Aina-chan needs a password to proceed! (╥﹏╥)")

    # Save all at once
    secrets.save()
    print("\n  ✅ Credentials saved to secrets.json ✨\n")

    return secrets


# ─── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Aina-chan's startup/shutdown handler! (◕‿◕✿)
    """
    print("\n🌟 Anita-CMS is starting up...")

    # Step 1: Make sure we have credentials
    secrets = _ensure_credentials()

    # Step 2: Initialize collections ONLY if credentials are configured
    if secrets.is_configured:
        _init_modules()
    else:
        print("  ⏭️  Skipping collection initialization")
        print("  💡  Complete setup at /auth/setup to initialize")

    yield  # App runs here

    print("🌙 Anita-CMS is shutting down...")


def _init_modules():
    """
    Initialize all module collections at startup.

    Aina-chan tries each one independently so if one fails,
    the others still work! (◕‿◕✿)
    """
    from backend.pages.service import PageService
    from backend.articles.service import ArticleService
    from backend.sites.service import SiteService
    from backend.collections.service import CollectionService
    from backend.storage.service import StorageService
    from backend.users.service import UserService

    init_tasks = [
        ("Pages", lambda: PageService().initialize()),
        ("Articles", lambda: ArticleService().initialize()),
        ("Sites", lambda: SiteService().initialize()),
        ("Collections", lambda: CollectionService().initialize()),
        ("Storage", lambda: StorageService().initialize()),
        ("Users", lambda: UserService().initialize()),
    ]

    for name, task in init_tasks:
        try:
            result = task()
            status = "✅" if result else "❌"
            print(f"  {status} {name}")
        except Exception as e:
            print(f"  ❌ {name} — {e}")

    print()  # Empty line for readability


# ─── App Instance ──────────────────────────────────────────────

app = FastAPI(
    title="Anita-CMS",
    description="""
        🎀 A modular, self-contained CMS built with FastAPI + PocketBase.

        ## Architecture
        Each module is **fully independent** and can be deleted without
        breaking the rest of the system!

        ## Modules
        - **Pages** — Simple static pages
        - **Articles** — Markdown-based blog content
        - **Sites** — HTML-based page content
        - **Collections** — Dynamic content type definitions
        - **Storage** — File and media metadata
        - **Users** — Role-based permission system
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─── CORS Middleware ────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Allow all during development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Include Routers ───────────────────────────────────────────
# Each module is 100% independent!
# Delete any line below without breaking the rest!

app.include_router(auth_router)         
app.include_router(pages_router)
app.include_router(article_router)
app.include_router(site_router)
app.include_router(collections_router)
app.include_router(storage_router)
app.include_router(users_router)


# ─── Root Endpoint ─────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """
    Welcome to Anita-CMS! 🎀

    Aina-chan's modular CMS system.
    Check out the docs at /docs for all available endpoints!
    """
    # Check if setup is needed
    from backend.util.secrets import SecretsManager
    is_configured = SecretsManager().is_configured

    return {
        "name": "Anita-CMS",
        "version": "0.1.0",
        "description": "A modular CMS built with FastAPI + PocketBase",
        "setup_required": not is_configured,
        "setup_url": "/auth/setup" if not is_configured else None,
        "docs": "/docs",
        "redoc": "/redoc",
        "modules": {
            "pages": {
                "path": "/pages",
                "description": "Simple static page management",
            },
            "articles": {
                "path": "/articles",
                "description": "Markdown-based blog content",
            },
            "sites": {
                "path": "/sites",
                "description": "HTML-based page content",
            },
            "collections": {
                "path": "/collections",
                "description": "Dynamic content type definitions",
            },
            "storage": {
                "path": "/storage",
                "description": "File and media metadata",
            },
            "users": {
                "path": "/users",
                "description": "Role-based permission system",
            },
        },
    }


# ─── Check Setup Status Endpoint ──────────────────────────────

@app.get("/api/setup/status", tags=["Setup"])
async def setup_status():
    """
    Check if Anita-CMS has been configured.

    Returns:
      configured: bool — Whether credentials and superuser exist
      step: str — "pending", "ready", "complete"
    """
    from backend.util.secrets import SecretsManager
    secrets = SecretsManager()

    if not secrets.is_configured:
        return {
            "configured": False,
            "step": "pending",
            "message": "Credentials not configured. Complete setup at /auth/setup",
        }

    # Check if superuser actually exists
    from backend.auth.manager import AuthManager
    manager = AuthManager()
    try:
        connection = manager.test_connection()
        if not connection.get("ok"):
            return {
                "configured": True,
                "step": "error",
                "message": f"Cannot connect to PocketBase: {connection.get('message')}",
            }

        has_superuser = manager.check_superuser_exists()
        if not has_superuser:
            return {
                "configured": True,
                "step": "ready",
                "message": "Credentials saved but superuser not created yet.",
            }

        return {
            "configured": True,
            "step": "complete",
            "message": "Anita-CMS is fully configured and ready!",
        }

    except Exception as e:
        return {
            "configured": True,
            "step": "error",
            "message": str(e),
        }


# ─── Health Check ──────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Aina-chan uses this to make sure the server is alive! (◕‿◕✿)
    """
    return {
        "status": "healthy",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


# ─── Main Entry Point ─────────────────────────────────────────

if __name__ == "__main__":
    """
    Aina-chan's direct run mode! (◕‿◕✿)

    Usage:
        uv run main.py                    # Terminal prompt (local dev)
        uv run main.py --web-setup        # Skip prompt, use web wizard
        SKIP_INIT=true uv run main.py     # Same as --web-setup
        python backend/main.py
    """
    import uvicorn

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))

    # Get host from environment or use default
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"🎀 Anita-CMS starting on http://{host}:{port}")
    print(f"📚 API Docs at http://{host}:{port}/docs")
    print()

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
