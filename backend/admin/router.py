import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.util.auth import require_superuser


templates = Jinja2Templates(directory="frontend")


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    # 🔐 No global dependency – pages are served freely,
    # the frontend JS handles authentication check.
)


# ─── Page Routes (unprotected – frontend handles auth) ────────

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_index(request: Request):
    return RedirectResponse(url="/admin/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse(
        "admin/dashboard/dashboard.html",
        {"request": request},
    )


@router.get("/pages", response_class=HTMLResponse)
async def admin_pages(request: Request):
    return templates.TemplateResponse(
        "admin/pages/pages.html",
        {"request": request},
    )


@router.get("/articles", response_class=HTMLResponse)
async def admin_articles(request: Request):
    return templates.TemplateResponse(
        "admin/articles/articles.html",
        {"request": request},
    )


@router.get("/sites", response_class=HTMLResponse)
async def admin_sites(request: Request):
    return templates.TemplateResponse(
        "admin/sites/sites.html",
        {"request": request},
    )


@router.get("/collections", response_class=HTMLResponse)
async def admin_collections(request: Request):
    return templates.TemplateResponse(
        "admin/collections/collections.html",
        {"request": request},
    )


@router.get("/storage", response_class=HTMLResponse)
async def admin_storage(request: Request):
    return templates.TemplateResponse(
        "admin/storage/storage.html",
        {"request": request},
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    return templates.TemplateResponse(
        "admin/users/users.html",
        {"request": request},
    )


# ─── Protected API Endpoints (only these require token) ───────

@router.get("/api/stats", dependencies=[Depends(require_superuser)])
async def admin_stats(request: Request):
    """Dashboard statistics – token required."""
    return {
        "pages": 0,
        "articles": 0,
        "sites": 0,
        "storage": 0,
        "users": 0,
    }
