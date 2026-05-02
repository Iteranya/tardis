from typing import Optional
from backend.articles.manager import ArticleManager
from backend.articles.schema import (
    ArticleCreate, ArticleUpdate, ArticleResponse,
    ArticleSummary,
)

class ArticleService:
    """
    Aina-chan's Business Logic Layer for Articles! (◕‿◕✿)

    This sits between the router and the manager, handling
    validation, transformations, and complex workflows.
    """

    def __init__(self):
        self.manager = ArticleManager()

    # ─── Lifecycle ────────────────────────────────────────────

    def initialize(self) -> bool:
        """Ensure the articles collection exists at startup."""
        return self.manager.ensure_collection_exists()

    # ─── CRUD with Business Logic ─────────────────────────────

    def create_article(self, data: ArticleCreate) -> Optional[ArticleResponse]:
        """
        Create a new article with slug uniqueness check.
        """
        # Check slug uniqueness
        if self.manager.slug_exists(data.slug):
            raise ValueError(
                f"An article with slug '{data.slug}' already exists! "
                f"Aina-chan can't have duplicates~ (╥﹏╥)"
            )

        result = self.manager.create_article(data.model_dump(exclude_unset=True))
        if not result:
            raise RuntimeError("Aina-chan couldn't create the article~")
        return ArticleResponse(**result)

    def get_article(self, article_id: str) -> Optional[ArticleResponse]:
        result = self.manager.get_article(article_id)
        if not result:
            return None
        return ArticleResponse(**result)

    def get_article_by_slug(self, slug: str) -> Optional[ArticleResponse]:
        result = self.manager.get_article_by_slug(slug)
        if not result:
            return None
        return ArticleResponse(**result)

    def update_article(self, article_id: str, data: ArticleUpdate) -> Optional[ArticleResponse]:
        """
        Update an article with slug uniqueness check.
        """
        # Check if exists
        existing = self.manager.get_article(article_id)
        if not existing:
            raise ValueError(f"Article '{article_id}' not found~")

        update_data = data.model_dump(exclude_unset=True)

        # Check slug uniqueness if changing
        if "slug" in update_data and update_data["slug"] != existing.get("slug"):
            if self.manager.slug_exists(update_data["slug"], exclude_id=article_id):
                raise ValueError(
                    f"Another article already has the slug '{update_data['slug']}'! "
                    f"Aina-chan can't allow duplicates~"
                )

        result = self.manager.update_article(article_id, update_data)
        if not result:
            raise RuntimeError("Aina-chan couldn't update the article~")
        return ArticleResponse(**result)

    def delete_article(self, article_id: str) -> bool:
        existing = self.manager.get_article(article_id)
        if not existing:
            raise ValueError(f"Article '{article_id}' not found~")
        return self.manager.delete_article(article_id)

    # ─── Listing ──────────────────────────────────────────────

    def list_articles(
        self,
        page: int = 1,
        per_page: int = 20,
        sort: str = "-sort_order",
        enabled: Optional[bool] = None,
        author: Optional[str] = None,
        label: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        result = self.manager.list_articles(
            page=page,
            per_page=per_page,
            sort=sort,
            enabled=enabled,
            author=author,
            label=label,
            tag=tag,
            search=search,
        )
        return {
            "items": [ArticleSummary(**item) for item in result.get("items", [])],
            "page": result.get("page", page),
            "per_page": result.get("perPage", per_page),
            "total_items": result.get("totalItems", 0),
            "total_pages": result.get("totalPages", 0),
        }

    def list_published_articles(
        self,
        page: int = 1,
        per_page: int = 20,
        sort: str = "-sort_order",
    ) -> dict:
        return self.list_articles(page=page, per_page=per_page, sort=sort, enabled=True)

    # ─── Publishing ───────────────────────────────────────────

    def publish_article(self, article_id: str) -> Optional[ArticleResponse]:
        result = self.manager.publish_article(article_id)
        if not result:
            raise RuntimeError("Aina-chan couldn't publish the article~")
        return ArticleResponse(**result)

    def unpublish_article(self, article_id: str) -> Optional[ArticleResponse]:
        result = self.manager.unpublish_article(article_id)
        if not result:
            raise RuntimeError("Aina-chan couldn't unpublish the article~")
        return ArticleResponse(**result)

    # ─── Slug Generation ──────────────────────────────────────

    def suggest_slug(self, title: str) -> str:
        """Generate a unique slug suggestion for the frontend."""
        return self.manager.generate_unique_slug(title)

    # ─── Stats ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return self.manager.get_stats()
