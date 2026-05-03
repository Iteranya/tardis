from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="frontend")

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_index(request: Request):
    """Serve the admin SPA shell."""
    return templates.TemplateResponse(
        "admin/index.html",
        {"request": request},
    )