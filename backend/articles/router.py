from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from backend.articles.service import ArticleService
from backend.articles.schema import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleSummaryListResponse,
)
router = APIRouter(
    prefix="/articles",
    tags=["Articles"],
)


def get_service() -> ArticleService:
    """Dependency: provide ArticleService with auto-init."""
    service = ArticleService()
    if not service.initialize():
        raise HTTPException(
            status_code=500,
            detail="Aina-chan couldn't initialize articles! (╥﹏╥)",
        )
    return service


@router.get("", response_model=ArticleSummaryListResponse)
async def list_articles(
    page: int = 1,
    per_page: int = 20,
    sort: str = "-sort_order",
    enabled: Optional[bool] = None,
    author: Optional[str] = None,
    label: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    service: ArticleService = Depends(get_service),
):
    """List articles with filters."""
    return service.list_articles(
        page=page,
        per_page=per_page,
        sort=sort,
        enabled=enabled,
        author=author,
        label=label,
        tag=tag,
        search=search,
    )


@router.post("", response_model=ArticleResponse, status_code=201)
async def create_article(
    data: ArticleCreate,
    service: ArticleService = Depends(get_service),
):
    """Create a new article."""
    try:
        return service.create_article(data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def article_stats(
    service: ArticleService = Depends(get_service),
):
    """Get article statistics."""
    return service.get_stats()


@router.get("/slug/suggest")
async def suggest_slug(
    title: str,
    service: ArticleService = Depends(get_service),
):
    """Suggest a unique slug for a given title."""
    slug = service.suggest_slug(title)
    return {"slug": slug, "title": title}


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    service: ArticleService = Depends(get_service),
):
    """Get an article by ID."""
    result = service.get_article(article_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find article '{article_id}'~ (╥﹏╥)",
        )
    return result


@router.get("/slug/{slug}", response_model=ArticleResponse)
async def get_article_by_slug(
    slug: str,
    service: ArticleService = Depends(get_service),
):
    """Get an article by slug."""
    result = service.get_article_by_slug(slug)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Aina-chan couldn't find article with slug '{slug}'~ (╥﹏╥)",
        )
    return result


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: str,
    data: ArticleUpdate,
    service: ArticleService = Depends(get_service),
):
    """Update an article."""
    try:
        return service.update_article(article_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: str,
    service: ArticleService = Depends(get_service),
):
    """Delete an article."""
    try:
        service.delete_article(article_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{article_id}/publish", response_model=ArticleResponse)
async def publish_article(
    article_id: str,
    service: ArticleService = Depends(get_service),
):
    """Publish an article (enable + promote draft to release)."""
    try:
        return service.publish_article(article_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{article_id}/unpublish", response_model=ArticleResponse)
async def unpublish_article(
    article_id: str,
    service: ArticleService = Depends(get_service),
):
    """Unpublish an article (disable only, content preserved)."""
    try:
        return service.unpublish_article(article_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))