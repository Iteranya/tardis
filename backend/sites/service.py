from typing import Optional
from backend.sites.manager import SiteManager
from backend.sites.schema import (
    SiteCreate, SiteUpdate, SiteResponse, SiteSummary,
)


class SiteService:
    """
    Aina-chan's Business Logic Layer for Sites! (◕‿◕✿)

    Handles validation, transformations, and complex workflows
    for HTML content entries.
    """

    def __init__(self):
        self.manager = SiteManager()

    # ─── Lifecycle ────────────────────────────────────────────

    def initialize(self) -> bool:
        return self.manager.ensure_collection_exists()

    # ─── CRUD with Business Logic ─────────────────────────────

    def create_site(self, data: SiteCreate) -> Optional[SiteResponse]:
        if self.manager.slug_exists(data.slug):
            raise ValueError(
                f"A site with slug '{data.slug}' already exists! "
                f"Aina-chan can't have duplicates~ (╥﹏╥)"
            )
        result = self.manager.create_site(data.model_dump(exclude_unset=True))
        if not result:
            raise RuntimeError("Aina-chan couldn't create the site~")
        return SiteResponse(**result)

    def get_site(self, site_id: str) -> Optional[SiteResponse]:
        result = self.manager.get_site(site_id)
        if not result:
            return None
        return SiteResponse(**result)

    def get_site_by_slug(self, slug: str) -> Optional[SiteResponse]:
        result = self.manager.get_site_by_slug(slug)
        if not result:
            return None
        return SiteResponse(**result)

    def update_site(self, site_id: str, data: SiteUpdate) -> Optional[SiteResponse]:
        existing = self.manager.get_site(site_id)
        if not existing:
            raise ValueError(f"Site '{site_id}' not found~")

        update_data = data.model_dump(exclude_unset=True)

        if "slug" in update_data and update_data["slug"] != existing.get("slug"):
            if self.manager.slug_exists(update_data["slug"], exclude_id=site_id):
                raise ValueError(
                    f"Another site already has the slug '{update_data['slug']}'!"
                )

        result = self.manager.update_site(site_id, update_data)
        if not result:
            raise RuntimeError("Aina-chan couldn't update the site~")
        return SiteResponse(**result)

    def delete_site(self, site_id: str) -> bool:
        existing = self.manager.get_site(site_id)
        if not existing:
            raise ValueError(f"Site '{site_id}' not found~")
        return self.manager.delete_site(site_id)

    # ─── Publishing ───────────────────────────────────────────

    def publish_site(self, site_id: str) -> Optional[SiteResponse]:
        result = self.manager.publish_site(site_id)
        if not result:
            raise RuntimeError("Aina-chan couldn't publish the site~")
        return SiteResponse(**result)

    def unpublish_site(self, site_id: str) -> Optional[SiteResponse]:
        result = self.manager.unpublish_site(site_id)
        if not result:
            raise RuntimeError("Aina-chan couldn't unpublish the site~")
        return SiteResponse(**result)

    # ─── Listing ──────────────────────────────────────────────

    def list_sites(
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
        result = self.manager.list_sites(
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
            "items": [SiteSummary(**item) for item in result.get("items", [])],
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
