from typing import Optional
from backend.pages.manager import PageManager
from backend.pages.schema import (
    PageCreate, PageUpdate, PageResponse, PageSummary,
)


class PageService:
    """
    Aina-chan's Business Logic Layer for Pages! (◕‿◕✿)

    Handles validation, transformations, and complex workflows.
    """

    def __init__(self):
        self.manager = PageManager()

    # ─── Lifecycle ────────────────────────────────────────────

    def initialize(self) -> bool:
        """Ensure the pages collection exists at startup."""
        return self.manager.ensure_collection_exists()

    # ─── CRUD with Business Logic ─────────────────────────────

    def create_page(self, data: PageCreate) -> Optional[PageResponse]:
        if self.manager.slug_exists(data.slug):
            raise ValueError(
                f"A page with slug '{data.slug}' already exists! "
                f"Aina-chan can't have duplicates~ (╥﹏╥)"
            )

        result = self.manager.create_page(data.model_dump(exclude_unset=True))
        if not result:
            raise RuntimeError("Aina-chan couldn't create the page~")
        return PageResponse(**result)

    def get_page(self, page_id: str) -> Optional[PageResponse]:
        result = self.manager.get_page(page_id)
        if not result:
            return None
        return PageResponse(**result)

    def get_page_by_slug(self, slug: str) -> Optional[PageResponse]:
        result = self.manager.get_page_by_slug(slug)
        if not result:
            return None
        return PageResponse(**result)

    def update_page(self, page_id: str, data: PageUpdate) -> Optional[PageResponse]:
        existing = self.manager.get_page(page_id)
        if not existing:
            raise ValueError(f"Page '{page_id}' not found~")

        update_data = data.model_dump(exclude_unset=True)

        if "slug" in update_data and update_data["slug"] != existing.get("slug"):
            if self.manager.slug_exists(update_data["slug"], exclude_id=page_id):
                raise ValueError(
                    f"Another page already has the slug '{update_data['slug']}'!"
                )

        result = self.manager.update_page(page_id, update_data)
        if not result:
            raise RuntimeError("Aina-chan couldn't update the page~")
        return PageResponse(**result)

    def delete_page(self, page_id: str) -> bool:
        existing = self.manager.get_page(page_id)
        if not existing:
            raise ValueError(f"Page '{page_id}' not found~")
        return self.manager.delete_page(page_id)

    # ─── Listing ──────────────────────────────────────────────

    def list_pages(
        self,
        page: int = 1,
        per_page: int = 20,
        sort: str = "-sort_order",
        enabled: Optional[bool] = None,
        label: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        result = self.manager.list_pages(
            page=page,
            per_page=per_page,
            sort=sort,
            enabled=enabled,
            label=label,
            tag=tag,
            search=search,
        )
        return {
            "items": [PageSummary(**item) for item in result.get("items", [])],
            "page": result.get("page", page),
            "per_page": result.get("perPage", per_page),
            "total_items": result.get("totalItems", 0),
            "total_pages": result.get("totalPages", 0),
        }

    # ─── Slug Generation ──────────────────────────────────────

    def suggest_slug(self, title: str) -> str:
        return self.manager.generate_unique_slug(title)

    # ─── Stats ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return self.manager.get_stats()
