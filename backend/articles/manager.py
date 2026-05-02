import os
import re
from typing import Optional
from pocketbase import PocketBase
from pocketbase.client import FileUpload
from backend.util.auth import authenticate_admin
from backend.util.pocketbase import collection_exists
from backend.util.secrets import SecretsManager


class ArticleManager:
    """
    Aina-chan's Article Manager! (◕‿◕✿)

    Fully self-contained module for the 'articles' collection.
    This can be deleted without breaking anything else!
    """

    COLLECTION_NAME = "sys_articles"

    # ─── Collection Schema ────────────────────────────────────
    # Self-contained! No external schema dependencies!

    @property
    def _collection_schema(self) -> dict:
        """The PocketBase schema for articles. Defined right here!"""
        return {
            "name": self.COLLECTION_NAME,
            "type": "base",
            "listRule": "",
            "viewRule": "",
            "createRule": "@request.auth.id != ''",
            "updateRule": "@request.auth.id != ''",
            "deleteRule": None,
            "indexes": [
                "CREATE UNIQUE INDEX `idx_articles_slug` ON `articles` (`slug`)",
                "CREATE INDEX `idx_articles_enabled_sort` ON `articles` (`enabled`, `sort_order`)",
            ],
            "fields": [
                {"name": "title", "type": "text", "required": True, "min": 1, "max": 200},
                {"name": "slug", "type": "text", "required": True, "min": 1, "max": 200, "pattern": "^[a-z0-9\\-]+$"},
                {"name": "desc", "type": "text", "required": False, "max": 500},
                {"name": "author", "type": "text", "required": False, "max": 100},
                {"name": "draft", "type": "editor", "required": False},
                {"name": "release", "type": "editor", "required": False},
                {"name": "thumb", "type": "file", "required": False, "maxSelect": 1, "maxSize": 5_242_880, "mimeTypes": ["image/jpeg", "image/png", "image/webp"]},
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

    # ─── Initialization ───────────────────────────────────────

    def __init__(self, pb_url=None, admin_email=None, admin_password=None):
        self._secrets = SecretsManager()
        self.pb_url = pb_url or self._secrets.pocketbase_url
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password
        self.client = PocketBase(self.pb_url)
        self._is_authenticated = False

    def authenticate_admin(self) -> bool:
        """Authenticate as superadmin for collection management."""
        if not self.admin_email or not self.admin_password:
            raise ValueError(
                "Aina-chan needs admin email and password to manage collections! ⊙﹏⊙"
            )

        try:
            result = authenticate_admin(
                self.client,
                self.admin_email,
                self.admin_password,
            )
            self._is_authenticated = result
            return result
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._is_authenticated = False
            return False
    def ensure_collection_exists(self) -> bool:
        if not self._is_authenticated:
            if not self.authenticate_admin():
                return False

        try:
            # Check if collection already exists
            try:
                self.client.collections.get_one(self.COLLECTION_NAME)
                return True
            except Exception as e:
                error_msg = str(e)
                # If the error is just SDK parsing (CollectionField 'help'), that's fine!
                if "CollectionField.__init__()" in error_msg and "help" in error_msg:
                    # Collection exists! SDK just can't parse the response.
                    return True

            # Try to create it
            self.client.collections.create(self._collection_schema)
            print(f"Aina-chan created the '{self.COLLECTION_NAME}' collection! ✨")
            return True

        except Exception as e:
            error_data = getattr(e, 'data', {})
            if isinstance(error_data, dict):
                data_field = error_data.get('data', {})
                if isinstance(data_field, dict):
                    name_error = data_field.get('name', {})
                    if isinstance(name_error, dict):
                        if name_error.get('code') == 'validation_collection_name_exists':
                            return True

            # Check for SDK parsing errors
            error_msg = str(e)
            if "CollectionField.__init__()" in error_msg and "help" in error_msg:
                return True

            print(f"Aina-chan encountered an error! {e} (╥﹏╥)")
            return False


    # ─── CRUD ─────────────────────────────────────────────────

    def create_article(self, data: dict) -> Optional[dict]:
        try:
            return self.client.collections.create(self.COLLECTION_NAME, data)
        except Exception as e:
            print(f"Aina-chan couldn't create the article! Error: {e} (╥﹏╥)")
            return None

    def get_article(self, article_id: str) -> Optional[dict]:
        try:
            return self.client.collections.get_one(self.COLLECTION_NAME, article_id)
        except Exception:
            return None

    def get_article_by_slug(self, slug: str) -> Optional[dict]:
        try:
            result = self.client.collections.get_list(
                self.COLLECTION_NAME,
                query_params={"filter": f'slug = "{slug}"', "limit": 1},
            )
            items = result.get("items", [])
            return items[0] if items else None
        except Exception:
            return None

    def update_article(self, article_id: str, data: dict) -> Optional[dict]:
        try:
            return self.client.collections.update(self.COLLECTION_NAME, article_id, data)
        except Exception as e:
            print(f"Aina-chan couldn't update the article! Error: {e} (╥﹏╥)")
            return None

    def delete_article(self, article_id: str) -> bool:
        try:
            self.client.collections.delete(self.COLLECTION_NAME, article_id)
            return True
        except Exception as e:
            print(f"Aina-chan couldn't delete the article! Error: {e} (╥﹏╥)")
            return False

    # ─── Listing with Filters ─────────────────────────────────

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

        try:
            params = {"page": page, "perPage": per_page, "sort": sort}
            if filter_str:
                params["filter"] = filter_str
            return self.client.collections.get_list(self.COLLECTION_NAME, query_params=params)
        except Exception as e:
            print(f"Aina-chan couldn't list articles! Error: {e} (╥﹏╥)")
            return {"items": [], "page": page, "perPage": per_page, "totalItems": 0, "totalPages": 0}

    # ─── Publishing Workflow ──────────────────────────────────

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

    # ─── Slug Utilities ───────────────────────────────────────

    def slug_exists(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        try:
            result = self.client.collections.get_list(
                self.COLLECTION_NAME,
                query_params={"filter": f'slug = "{slug}"', "limit": 1},
            )
            items = result.get("items", [])
            if not items:
                return False
            if exclude_id:
                return items[0]["id"] != exclude_id
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

    # ─── File Uploads ─────────────────────────────────────────

    def upload_thumbnail(self, article_id: str, file_path: str) -> Optional[dict]:
        try:
            with open(file_path, "rb") as f:
                file_upload = FileUpload(
                    filename=os.path.basename(file_path),
                    data=f.read(),
                    content_type="image/jpeg",
                )
            return self.client.collections.update(
                self.COLLECTION_NAME, article_id, {"thumb": file_upload}
            )
        except Exception as e:
            print(f"Aina-chan couldn't upload thumbnail! Error: {e} (╥﹏╥)")
            return None

    # ─── Stats ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        total = 0
        published = 0
        try:
            total_result = self.client.collections.get_list(
                self.COLLECTION_NAME, query_params={"perPage": 1}
            )
            total = total_result.get("totalItems", 0)

            published_result = self.client.collections.get_list(
                self.COLLECTION_NAME,
                query_params={"perPage": 1, "filter": "enabled = true"},
            )
            published = published_result.get("totalItems", 0)
        except Exception:
            pass

        return {
            "total_articles": total,
            "published_articles": published,
            "draft_articles": total - published,
        }
