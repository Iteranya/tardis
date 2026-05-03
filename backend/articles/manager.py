import re
import httpx
from typing import Optional
from backend.util.secrets import get_secrets
from backend.util.const import COLLECTION_ARTICLES


class ArticleManager:
    """
    Aina-chan's 100% SDK‑free Article Manager!
    Only httpx + raw REST API calls! (◕‿◕✿)
    """

    COLLECTION_NAME = COLLECTION_ARTICLES

    # ─── Collection Schema ──────────────────────────────────────
    @property
    def _collection_schema(self) -> dict:
        table = self.COLLECTION_NAME
        return {
            "name": table,
            "type": "base",
            "listRule": "",
            "viewRule": "",
            "createRule": "@request.auth.id != ''",
            "updateRule": "@request.auth.id != ''",
            "deleteRule": None,
            "indexes": [
                f"CREATE UNIQUE INDEX `idx_{table}_slug` ON `{table}` (`slug`)",
                f"CREATE INDEX `idx_{table}_enabled_sort` ON `{table}` (`enabled`, `sort_order`)",
            ],
            "fields": [
                {"name": "title", "type": "text", "required": True, "min": 1, "max": 200},
                {"name": "slug", "type": "text", "required": True, "min": 1, "max": 200,
                 "pattern": "^[a-z0-9\\-]+$"},
                {"name": "desc", "type": "text", "required": False, "max": 500},
                {"name": "author", "type": "text", "required": False, "max": 100},
                {"name": "draft", "type": "text", "required": False},
                {"name": "release", "type": "text", "required": False},
                {"name": "thumb", "type": "text", "required": False},
                {"name": "gallery", "type": "json", "required": False},
                {"name": "labels", "type": "json", "required": False},
                {"name": "tags", "type": "json", "required": False},
                {"name": "enabled", "type": "bool", "required": False},
                {"name": "sort_order", "type": "number", "required": False, "noDecimal": True, "min": 0},
                {"name": "custom", "type": "json", "required": False},
                {"name": "created", "type": "autodate", "onCreate": True, "onUpdate": False},
                {"name": "updated", "type": "autodate", "onCreate": True, "onUpdate": True},
            ],
        }

    # ─── Initialization ─────────────────────────────────────────
    def __init__(self, pb_url=None, admin_email=None, admin_password=None):
        self._secrets = get_secrets()
        # No PocketBase SDK – just httpx
        self.pb_url = (pb_url or self._secrets.pocketbase_url).rstrip('/')
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password
        # httpx client with base URL
        self.client = httpx.Client(base_url=self.pb_url, timeout=30.0)
        self._token = None
        self._admin_id = None

    # ─── Admin Authentication via API ───────────────────────────
    def authenticate_admin(self) -> bool:
        """Authenticate using PocketBase REST API directly."""
        if not self.admin_email or not self.admin_password:
            raise ValueError("Aina-chan needs admin email and password! ⊙﹏⊙")
        try:
            resp = self.client.post(
                "/api/admins/auth-with-password",
                json={"identity": self.admin_email, "password": self.admin_password},
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["token"]
            self._admin_id = data["admin"]["id"]
            # Set default auth header for all future requests
            self.client.headers["Authorization"] = f"Bearer {self._token}"
            return True
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._token = None
            self._admin_id = None
            return False

    # ─── Collection Management ───────────────────────────────────
    def ensure_collection_exists(self) -> bool:
        if not self._token and not self.authenticate_admin():
            return False
        try:
            resp = self.client.get(f"/api/collections/{self.COLLECTION_NAME}")
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        try:
            resp = self.client.post("/api/collections", json=self._collection_schema)
            resp.raise_for_status()
            print(f"Aina-chan created the '{self.COLLECTION_NAME}' collection! ✨")
            return True
        except Exception as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    err = e.response.json()
                    if err.get('data', {}).get('name', {}).get('code') == 'validation_collection_name_exists':
                        return True
                except Exception:
                    pass
            print(f"Aina-chan couldn't create collection! Error: {e} (╥﹏╥)")
            return False

    # ─── Record helpers ─────────────────────────────────────────
    def _record_url(self, record_id: str = None) -> str:
        base = f"/api/collections/{self.COLLECTION_NAME}/records"
        return f"{base}/{record_id}" if record_id else base

    # ─── CRUD ───────────────────────────────────────────────────
    def create_article(self, data: dict) -> Optional[dict]:
        try:
            resp = self.client.post(self._record_url(), json=data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Aina-chan couldn't create article! Error: {e} (╥﹏╥)")
            return None

    def get_article(self, article_id: str) -> Optional[dict]:
        try:
            resp = self.client.get(self._record_url(article_id))
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def get_article_by_slug(self, slug: str) -> Optional[dict]:
        try:
            # PocketBase expects filter to be URL‑encoded; httpx does that automatically
            filter_str = f'slug = "{slug}"'
            params = {"filter": filter_str, "perPage": 1}
            resp = self.client.get(self._record_url(), params=params)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            return items[0] if items else None
        except Exception as e:
            print(f"Aina-chan couldn't fetch by slug! Error: {e} (╥﹏╥)")
            return None

    def update_article(self, article_id: str, data: dict) -> Optional[dict]:
        try:
            resp = self.client.patch(self._record_url(article_id), json=data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Aina-chan couldn't update article! Error: {e} (╥﹏╥)")
            return None

    def delete_article(self, article_id: str) -> bool:
        try:
            resp = self.client.delete(self._record_url(article_id))
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"Aina-chan couldn't delete article! Error: {e} (╥﹏╥)")
            return False

    # ─── Listing with filters ──────────────────────────────────
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
        filters = []
        if enabled is not None:
            filters.append(f"enabled = {str(enabled).lower()}")
        if author:
            filters.append(f'author = "{author}"')
        if label:
            filters.append(f'labels ~ "{label}"')
        if tag:
            filters.append(f'tags ~ "{tag}"')
        if search:
            filters.append(f'(title ~ "{search}" || desc ~ "{search}" || release ~ "{search}")')

        filter_str = " && ".join(filters) if filters else None

        params = {"page": page, "perPage": per_page, "sort": sort}
        if filter_str:
            params["filter"] = filter_str

        try:
            resp = self.client.get(self._record_url(), params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Aina-chan couldn't list articles! Error: {e} (╥﹏╥)")
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

    # ─── Publishing workflow ──────────────────────────────────
    def publish_article(self, article_id: str, promote_draft: bool = True) -> Optional[dict]:
        article = self.get_article(article_id)
        if not article:
            return None
        update_data = {"enabled": True}
        if promote_draft:
            draft = article.get("draft")
            release = article.get("release")
            if draft and not release:
                update_data["release"] = draft
                update_data["draft"] = None
        return self.update_article(article_id, update_data)

    def unpublish_article(self, article_id: str) -> Optional[dict]:
        return self.update_article(article_id, {"enabled": False})

    # ─── Slug utilities ────────────────────────────────────────
    def slug_exists(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        try:
            filter_str = f'slug = "{slug}"'
            params = {"filter": filter_str, "perPage": 1}
            resp = self.client.get(self._record_url(), params=params)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if not items:
                return False
            if exclude_id and items[0]["id"] == exclude_id:
                return False
            return True
        except Exception:
            return False

    def generate_slug(self, title: str) -> str:
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    def generate_unique_slug(self, title: str) -> str:
        base = self.generate_slug(title)
        slug = base
        counter = 1
        while self.slug_exists(slug):
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    # ─── Stats ─────────────────────────────────────────────────
    def get_stats(self) -> dict:
        total = 0
        published = 0
        try:
            resp = self.client.get(self._record_url(), params={"perPage": 1})
            resp.raise_for_status()
            total = resp.json().get("totalItems", 0)

            resp = self.client.get(
                self._record_url(), params={"perPage": 1, "filter": "enabled = true"}
            )
            resp.raise_for_status()
            published = resp.json().get("totalItems", 0)
        except Exception as e:
            print(f"Aina-chan stats error: {e} (╥﹏╥)")
        return {
            "total_articles": total,
            "published_articles": published,
            "draft_articles": total - published,
        }

    # ─── Cleanup ────────────────────────────────────────────────
    def close(self):
        self.client.close()
