import os
from typing import Optional
from pocketbase import PocketBase
from pocketbase.client import FileUpload
from util.secrets import SecretsManager


class PageCollectionManager:
    """
    Aina-chan's PocketBase Page Collection Manager! (◕‿◕✿)

    Handles initialization and CRUD for the 'pages' collection.
    """

    def __init__(
        self,
        pb_url: Optional[str] = None,
        admin_email: Optional[str] = None,
        admin_password: Optional[str] = None,
    ):
        """
        Initialize the manager with PocketBase connection.

        Falls back to SecretsManager if credentials aren't provided directly!
        """
        # Load secrets from the manager
        self._secrets = SecretsManager()

        # Use provided values, or fall back to secrets.json
        self.pb_url = pb_url or self._secrets.pocketbase_url
        self.admin_email = admin_email or self._secrets.admin_email
        self.admin_password = admin_password or self._secrets.admin_password

        self.client = PocketBase(self.pb_url)
        self._is_authenticated = False

    # --- Authentication ---

    def authenticate_admin(self) -> bool:
        """Authenticate as superadmin for collection management."""
        if not self.admin_email or not self.admin_password:
            raise ValueError(
                "Aina-chan needs admin email and password to manage collections! ⊙﹏⊙"
            )

        try:
            self.client.admins.auth_with_password(
                self.admin_email,
                self.admin_password,
            )
            self._is_authenticated = True
            return True
        except Exception as e:
            print(f"Aina-chan couldn't authenticate! Error: {e} (╥﹏╥)")
            self._is_authenticated = False
            return False

    # --- Collection Schema ---

    @property
    def _page_schema(self) -> dict:
        """The full schema for the 'pages' collection."""
        return {
            "name": "pages",
            "type": "base",
            "listRule": "",
            "viewRule": "",
            "createRule": "@request.auth.id != ''",
            "updateRule": "@request.auth.id != ''",
            "deleteRule": None,
            "indexes": [
                "CREATE UNIQUE INDEX `idx_pages_slug` ON `pages` (`slug`)"
            ],
            "fields": [
                {
                    "name": "title",
                    "type": "text",
                    "required": True,
                    "min": 1,
                    "max": 200,
                },
                {
                    "name": "slug",
                    "type": "text",
                    "required": True,
                    "min": 1,
                    "max": 200,
                    "pattern": "^[a-z0-9\\-]+$",
                },
                {
                    "name": "desc",
                    "type": "text",
                    "required": False,
                    "max": 500,
                },
                {
                    "name": "content_id",
                    "type": "text",
                    "required": False,
                },
                {
                    "name": "thumb",
                    "type": "file",
                    "required": False,
                    "maxSelect": 1,
                    "maxSize": 5_242_880,
                    "mimeTypes": [
                        "image/jpeg",
                        "image/png",
                        "image/webp",
                    ],
                },
                {
                    "name": "labels",
                    "type": "json",
                    "required": False,
                },
                {
                    "name": "tags",
                    "type": "json",
                    "required": False,
                },
                {
                    "name": "enabled",
                    "type": "bool",
                    "required": False,
                },
                {
                    "name": "sort_order",
                    "type": "number",
                    "required": False,
                    "noDecimal": True,
                    "min": 0,
                },
                {
                    "name": "custom",
                    "type": "json",
                    "required": False,
                },
                {
                    "name": "created",
                    "type": "autodate",
                    "onCreate": True,
                    "onUpdate": False,
                },
                {
                    "name": "updated",
                    "type": "autodate",
                    "onCreate": True,
                    "onUpdate": True,
                },
            ],
        }

    # --- Collection Initialization ---

    def ensure_collection_exists(self) -> bool:
        """Check if 'pages' collection exists, create if not."""
        if not self._is_authenticated:
            if not self.authenticate_admin():
                return False

        try:
            try:
                self.client.collections.get_one("pages")
                return True
            except Exception:
                self.client.collections.create(self._page_schema)
                print("Aina-chan created the 'pages' collection! ✨")
                return True
        except Exception as e:
            print(f"Aina-chan encountered an error! {e} (╥﹏╥)")
            return False

    # --- CRUD Operations ---

    def create_page(self, data: dict) -> Optional[dict]:
        """Create a new page record."""
        try:
            return self.client.collections.create("pages", data)
        except Exception as e:
            print(f"Aina-chan couldn't create the page! Error: {e} (╥﹏╥)")
            return None

    def get_page(self, page_id: str) -> Optional[dict]:
        """Get a single page by its ID."""
        try:
            return self.client.collections.get_one("pages", page_id)
        except Exception as e:
            print(f"Aina-chan couldn't find that page! Error: {e} (╥﹏╥)")
            return None

    def get_page_by_slug(self, slug: str) -> Optional[dict]:
        """Get a single page by its slug."""
        try:
            result = self.client.collections.get_list(
                "pages",
                query_params={
                    "filter": f'slug = "{slug}"',
                    "limit": 1,
                },
            )
            items = result.get("items", [])
            return items[0] if items else None
        except Exception as e:
            print(f"Aina-chan couldn't find that page! Error: {e} (╥﹏╥)")
            return None

    def update_page(self, page_id: str, data: dict) -> Optional[dict]:
        """Update an existing page record."""
        try:
            return self.client.collections.update("pages", page_id, data)
        except Exception as e:
            print(f"Aina-chan couldn't update the page! Error: {e} (╥﹏╥)")
            return None

    def delete_page(self, page_id: str) -> bool:
        """Delete a page by its ID."""
        try:
            self.client.collections.delete("pages", page_id)
            return True
        except Exception as e:
            print(f"Aina-chan couldn't delete the page! Error: {e} (╥﹏╥)")
            return False

    def list_pages(
        self,
        page: int = 1,
        per_page: int = 20,
        sort: str = "-sort_order",
        filter: Optional[str] = None,
    ) -> dict:
        """List pages with pagination, sorting, and filtering."""
        try:
            params = {
                "page": page,
                "perPage": per_page,
                "sort": sort,
            }
            if filter:
                params["filter"] = filter

            return self.client.collections.get_list(
                "pages",
                query_params=params,
            )
        except Exception as e:
            print(f"Aina-chan couldn't list pages! Error: {e} (╥﹏╥)")
            return {
                "items": [],
                "page": page,
                "perPage": per_page,
                "totalItems": 0,
                "totalPages": 0,
            }

    # --- Convenience: Upload Thumbnail ---

    def upload_thumbnail(self, page_id: str, file_path: str) -> Optional[dict]:
        """Upload a thumbnail image for a page."""
        try:
            with open(file_path, "rb") as f:
                file_upload = FileUpload(
                    filename=os.path.basename(file_path),
                    data=f.read(),
                    content_type="image/jpeg",
                )

            return self.client.collections.update(
                "pages",
                page_id,
                {"thumb": file_upload},
            )
        except Exception as e:
            print(f"Aina-chan couldn't upload the thumbnail! Error: {e} (╥﹏╥)")
            return None
