import json
import os
from typing import Optional, Dict, List, Any
from util.secrets import SecretsManager


class SitemapManager:
    """
    Aina-chan's Sitemap Manager! (◕‿◕✿)

    Manages a sitemap.json file that maps URL paths to PocketBase page IDs.
    Supports groups (like 'home', 'character') and entries within each group.

    Structure:
    {
        "groups": {
            "home": {
                "slug": "",               # Base slug for the group
                "entries": {
                    "": {                   # Entry slug (empty for root)
                        "page_id": "...",
                        "title": "Home",
                        "enabled": true
                    }
                }
            },
            "character": {
                "slug": "character",
                "entries": {
                    "aina": {
                        "page_id": "...",
                        "title": "Aina-chan's Page",
                        "enabled": true
                    }
                }
            }
        }
    }

    URL paths are built as: /{group_slug}/{entry_slug}
    The home group with empty slug produces just "/"
    """

    def __init__(self, root_dir: Optional[str] = None):
        """
        Initialize the SitemapManager.

        Args:
            root_dir: Project root where sitemap.json lives.
                      If None, Aina will detect it automatically.
        """
        self._secrets = SecretsManager(root_dir)
        self.root_dir = self._secrets.root_dir
        self.sitemap_path = os.path.join(self.root_dir, "sitemap.json")
        self._data: Dict[str, Any] = {}
        self._load_or_initialize()

    # ─── Load / Initialize ───────────────────────────────────────

    def _default_sitemap(self) -> dict:
        """
        Default sitemap structure with a home group as an example.

        Aina-chan sets up a home group with an empty entry so
        Senpai's site has a root page ready to configure! ✨
        """
        return {
            "groups": {
                "home": {
                    "slug": "",
                    "description": "Home page group",
                    "entries": {
                        "": {
                            "page_id": "",
                            "title": "Home",
                            "enabled": False,
                        }
                    },
                }
            }
        }

    def _load_or_initialize(self) -> None:
        """Load sitemap.json or create default if missing."""
        if os.path.exists(self.sitemap_path):
            try:
                with open(self.sitemap_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                print(
                    f"Aina-chan loaded sitemap from {self.sitemap_path} ✨"
                )
            except (json.JSONDecodeError, IOError) as e:
                print(
                    f"Aina-chan couldn't read sitemap.json! "
                    f"Error: {e} (╥﹏╥)"
                )
                print("Aina-chan will create a fresh one~")
                self._data = self._default_sitemap()
                self.save()
        else:
            print(
                f"Aina-chan didn't find sitemap.json... "
                f"Creating one at {self.sitemap_path} (｀・ω・´)"
            )
            self._data = self._default_sitemap()
            self.save()

    def save(self) -> bool:
        """Save current sitemap data to file."""
        try:
            os.makedirs(self.root_dir, exist_ok=True)
            with open(self.sitemap_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Aina-chan couldn't save sitemap! Error: {e} (╥﹏╥)")
            return False

    # ─── Group Management ────────────────────────────────────────

    def add_group(
        self,
        group_name: str,
        slug: str,
        description: str = "",
    ) -> bool:
        """
        Add a new group to the sitemap.

        Args:
            group_name: Identifier for the group (e.g., "character")
            slug: URL segment for the group (e.g., "character")
                  Use empty string "" for the root group.
            description: Optional description for the group.

        Example:
            manager.add_group("character", "character", "Character pages")
            # Creates /character/... routes
        """
        if group_name in self._data["groups"]:
            print(
                f"Aina-chan says group '{group_name}' already exists! "
                f"Use update_group() if Senpai wants to change it~ (◕‿◕✿)"
            )
            return False

        self._data["groups"][group_name] = {
            "slug": slug,
            "description": description,
            "entries": {},
        }
        self.save()
        print(
            f"Aina-chan created group '{group_name}' with slug '/{slug}' ✨"
        )
        return True

    def remove_group(self, group_name: str) -> bool:
        """
        Remove a group and all its entries from the sitemap.

        Warning: This will delete all routes under this group!
        """
        if group_name not in self._data["groups"]:
            print(
                f"Aina-chan couldn't find group '{group_name}'~ (╥﹏╥)"
            )
            return False

        del self._data["groups"][group_name]
        self.save()
        print(
            f"Aina-chan removed group '{group_name}' and all its entries~"
        )
        return True

    def rename_group(self, old_name: str, new_name: str) -> bool:
        """Rename a group while keeping its contents."""
        if old_name not in self._data["groups"]:
            print(
                f"Aina-chan couldn't find group '{old_name}'~ (╥﹏╥)"
            )
            return False
        if new_name in self._data["groups"]:
            print(
                f"Aina-chan says group '{new_name}' already exists! "
                f"Can't rename~ (◕‿◕;)"
            )
            return False

        self._data["groups"][new_name] = self._data["groups"].pop(old_name)
        self.save()
        return True

    def get_group(self, group_name: str) -> Optional[dict]:
        """Get a group's data including its entries."""
        return self._data["groups"].get(group_name)

    def get_all_groups(self) -> Dict[str, dict]:
        """Get all groups with their entries."""
        return self._data["groups"].copy()

    def list_groups(self) -> List[str]:
        """List all group names."""
        return list(self._data["groups"].keys())

    # ─── Entry Management ────────────────────────────────────────

    def add_entry(
        self,
        group_name: str,
        entry_slug: str,
        page_id: str,
        title: str = "",
        enabled: bool = True,
    ) -> bool:
        """
        Add a new entry (route) under a specific group.

        Args:
            group_name: Which group this entry belongs to.
            entry_slug: URL slug for this specific entry.
                        Use "" for group root (e.g., home group root).
            page_id: The PocketBase page record ID.
            title: Human-readable title for the route.
            enabled: Whether this route is active.

        Example:
            manager.add_entry("character", "aina", "PAGE_ID_HERE",
                              "Aina-chan's Page")
            # Creates route: /character/aina
        """
        if group_name not in self._data["groups"]:
            print(
                f"Aina-chan couldn't find group '{group_name}'! "
                f"Use add_group() first~ (╥﹏╥)"
            )
            return False

        if entry_slug in self._data["groups"][group_name]["entries"]:
            print(
                f"Entry '/{entry_slug}' already exists in group "
                f"'{group_name}'! Use update_entry() to modify~"
            )
            return False

        self._data["groups"][group_name]["entries"][entry_slug] = {
            "page_id": page_id,
            "title": title or entry_slug,
            "enabled": enabled,
        }
        self.save()
        path = self._build_path(group_name, entry_slug)
        print(
            f"Aina-chan added route '{path}' → page ID '{page_id}' ✨"
        )
        return True

    def update_entry(
        self,
        group_name: str,
        entry_slug: str,
        page_id: Optional[str] = None,
        title: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> bool:
        """
        Update an existing entry's properties.

        Only provided fields will be updated.
        """
        if group_name not in self._data["groups"]:
            print(f"Aina-chan couldn't find group '{group_name}'~ (╥﹏╥)")
            return False

        entries = self._data["groups"][group_name]["entries"]
        if entry_slug not in entries:
            print(
                f"Aina-chan couldn't find entry '{entry_slug}' in "
                f"group '{group_name}'~ (╥﹏╥)"
            )
            return False

        if page_id is not None:
            entries[entry_slug]["page_id"] = page_id
        if title is not None:
            entries[entry_slug]["title"] = title
        if enabled is not None:
            entries[entry_slug]["enabled"] = enabled

        self.save()
        path = self._build_path(group_name, entry_slug)
        print(f"Aina-chan updated route '{path}' ✨")
        return True

    def remove_entry(self, group_name: str, entry_slug: str) -> bool:
        """Remove a specific entry from a group."""
        if group_name not in self._data["groups"]:
            print(f"Aina-chan couldn't find group '{group_name}'~ (╥﹏╥)")
            return False

        entries = self._data["groups"][group_name]["entries"]
        if entry_slug not in entries:
            print(
                f"Aina-chan couldn't find entry '{entry_slug}' in "
                f"group '{group_name}'~ (╥﹏╥)"
            )
            return False

        del entries[entry_slug]
        self.save()
        print(
            f"Aina-chan removed entry '{entry_slug}' from group "
            f"'{group_name}'~"
        )
        return True

    def get_entry(self, group_name: str, entry_slug: str) -> Optional[dict]:
        """Get a specific entry's data."""
        group = self._data["groups"].get(group_name)
        if not group:
            return None
        return group["entries"].get(entry_slug)

    # ─── Path Resolution ─────────────────────────────────────────

    def _build_path(self, group_name: str, entry_slug: str) -> str:
        """
        Build the full URL path from group and entry slugs.

        Examples:
            group "home" (slug=""), entry ""        → "/"
            group "character" (slug="character"), entry "aina" → "/character/aina"
            group "character" (slug="character"), entry ""     → "/character"
        """
        group = self._data["groups"].get(group_name, {})
        group_slug = group.get("slug", "")

        if group_slug and entry_slug:
            return f"/{group_slug}/{entry_slug}"
        elif group_slug and not entry_slug:
            return f"/{group_slug}"
        elif not group_slug and entry_slug:
            return f"/{entry_slug}"
        else:
            return "/"

    def get_page_id_by_path(self, path: str) -> Optional[str]:
        """
        Resolve a URL path to a PocketBase page ID.

        Args:
            path: URL path like "/", "/character/aina", "/character"

        Returns:
            Page ID if found, None otherwise.

        This method does NOT check enabled status.
        Use get_active_page_id_by_path() for that.
        """
        # Normalize path
        path = path.rstrip("/") or "/"

        # Search through all groups and entries
        for group_name, group in self._data["groups"].items():
            group_slug = group.get("slug", "")

            # Build the base path for this group
            if group_slug:
                base_path = f"/{group_slug}"
            else:
                base_path = "/"

            # Check if the path matches this group
            if path == base_path:
                # Root entry of the group
                entry = group["entries"].get("")
                if entry:
                    return entry["page_id"]
                else:
                    # No root entry for this group
                    # Maybe there's an entry with the same slug as group?
                    # This is ambiguous, so skip
                    continue

            # Check if path starts with group base
            if base_path != "/" and path.startswith(base_path + "/"):
                # Extract the entry slug
                entry_slug = path[len(base_path) + 1:]
                entry = group["entries"].get(entry_slug)
                if entry:
                    return entry["page_id"]

            # Special case: group slug is empty (home group)
            if base_path == "/" and path != "/":
                # Path like "/something" might be an entry in home group
                entry_slug = path.lstrip("/")
                entry = group["entries"].get(entry_slug)
                if entry:
                    return entry["page_id"]

        return None

    def get_active_page_id_by_path(
        self,
        path: str,
        page_manager=None,
    ) -> Optional[str]:
        """
        Resolve a URL path to a page ID, but only if the page is enabled.

        Args:
            path: URL path to resolve.
            page_manager: Optional PageCollectionManager to check
                          enabled status in PocketBase directly.
                          If not provided, uses the 'enabled' field
                          stored in the sitemap entry.

        Returns:
            Page ID if the page exists and is enabled, None otherwise.
        """
        # First try to get the entry from sitemap
        page_id = self.get_page_id_by_path(path)
        if not page_id:
            return None

        # If page_manager is provided, verify enabled status in PocketBase
        if page_manager:
            try:
                page = page_manager.get_page(page_id)
                if page and page.get("enabled"):
                    return page_id
                return None
            except Exception:
                return None

        # Fallback: check the enabled flag stored in sitemap entry
        entry = self._find_entry_by_path(path)
        if entry and entry.get("enabled"):
            return page_id

        return None

    def _find_entry_by_path(self, path: str) -> Optional[dict]:
        """
        Find the full entry dict by path (internal helper).
        """
        path = path.rstrip("/") or "/"

        for group_name, group in self._data["groups"].items():
            group_slug = group.get("slug", "")
            base_path = f"/{group_slug}" if group_slug else "/"

            if path == base_path:
                entry = group["entries"].get("")
                if entry:
                    return entry

            if base_path != "/" and path.startswith(base_path + "/"):
                entry_slug = path[len(base_path) + 1:]
                entry = group["entries"].get(entry_slug)
                if entry:
                    return entry

            if base_path == "/" and path != "/":
                entry_slug = path.lstrip("/")
                entry = group["entries"].get(entry_slug)
                if entry:
                    return entry

        return None

    # ─── Active Routes (Enabled Only) ────────────────────────────

    def get_active_routes(
        self,
        page_manager=None,
    ) -> Dict[str, str]:
        """
        Get a dictionary of all active routes: path → page_id.

        Only includes entries where:
        - The sitemap entry has enabled=True
        - AND (if page_manager provided) the page is enabled in PocketBase

        Returns:
            {"path": "page_id", ...}
        """
        routes = {}

        for group_name, group in self._data["groups"].items():
            group_slug = group.get("slug", "")

            for entry_slug, entry in group["entries"].items():
                if not entry.get("enabled", False):
                    continue

                path = self._build_path(group_name, entry_slug)
                page_id = entry["page_id"]

                # If page_manager is available, double-check with PocketBase
                if page_manager:
                    try:
                        page = page_manager.get_page(page_id)
                        if page and page.get("enabled"):
                            routes[path] = page_id
                    except Exception:
                        # If we can't fetch, trust the sitemap entry
                        routes[path] = page_id
                else:
                    routes[path] = page_id

        return routes

    def get_active_routes_tree(
        self,
        page_manager=None,
    ) -> List[dict]:
        """
        Get a nested tree structure of active routes.

        Useful for generating navigation menus!

        Returns a list of group dicts:
        [
            {
                "group": "home",
                "slug": "",
                "path": "/",
                "entries": [
                    {"slug": "", "path": "/", "title": "Home", "page_id": "..."}
                ]
            },
            {
                "group": "character",
                "slug": "character",
                "path": "/character",
                "entries": [
                    {"slug": "aina", "path": "/character/aina", "title": "Aina", ...},
                    {"slug": "anita", "path": "/character/anita", "title": "Anita", ...}
                ]
            }
        ]
        """
        tree = []

        for group_name, group in self._data["groups"].items():
            group_slug = group.get("slug", "")
            group_path = f"/{group_slug}" if group_slug else "/"

            entries = []
            for entry_slug, entry in group["entries"].items():
                if not entry.get("enabled", False):
                    continue

                path = self._build_path(group_name, entry_slug)
                page_id = entry["page_id"]

                # Optional PocketBase verification
                if page_manager:
                    try:
                        page = page_manager.get_page(page_id)
                        if page and not page.get("enabled"):
                            continue
                    except Exception:
                        pass

                entries.append({
                    "slug": entry_slug,
                    "path": path,
                    "title": entry.get("title", entry_slug),
                    "page_id": page_id,
                })

            # Only include groups that have active entries
            if entries:
                tree.append({
                    "group": group_name,
                    "slug": group_slug,
                    "path": group_path,
                    "description": group.get("description", ""),
                    "entries": entries,
                })

        return tree

    # ─── Convenience Methods ─────────────────────────────────────

    def get_all_page_ids(self) -> List[str]:
        """Get all page IDs stored in the sitemap (regardless of enabled)."""
        ids = []
        for group in self._data["groups"].values():
            for entry in group["entries"].values():
                if entry["page_id"]:
                    ids.append(entry["page_id"])
        return ids

    def sync_from_pages(
        self,
        pages: List[dict],
        group_name: str = "pages",
        group_slug: str = "",
    ) -> int:
        """
        Bulk add/update entries from a list of page dicts.

        Each page dict should have: id, slug, title, enabled

        Aina-chan will create the group if it doesn't exist,
        and add all pages as entries! (◕‿◕✿)

        Returns the number of entries added/updated.
        """
        if group_name not in self._data["groups"]:
            self.add_group(group_name, group_slug,
                           "Auto-synced from pages")

        count = 0
        for page in pages:
            page_id = page.get("id")
            slug = page.get("slug", "")
            title = page.get("title", slug)
            enabled = page.get("enabled", False)

            if page_id and slug:
                # Check if entry exists
                existing = self.get_entry(group_name, slug)
                if existing:
                    self.update_entry(
                        group_name, slug,
                        page_id=page_id,
                        title=title,
                        enabled=enabled,
                    )
                else:
                    self.add_entry(
                        group_name, slug, page_id,
                        title=title, enabled=enabled,
                    )
                count += 1

        self.save()
        print(
            f"Aina-chan synced {count} pages into group '{group_name}' ✨"
        )
        return count

    # ─── Display ─────────────────────────────────────────────────

    def print_sitemap(self) -> None:
        """
        Print a beautiful tree of the current sitemap to console.

        Aina-chan loves seeing the structure! (◕‿◕✿)
        """
        print("\n" + "=" * 50)
        print("  🗺️  Aina-chan's Sitemap")
        print("=" * 50)

        for group_name, group in self._data["groups"].items():
            group_slug = group.get("slug", "")
            group_path = f"/{group_slug}" if group_slug else "/"
            print(f"\n  📂 {group_name} ({group_path})")
            print(f"     {group.get('description', '')}")

            for entry_slug, entry in group["entries"].items():
                path = self._build_path(group_name, entry_slug)
                status = "✅" if entry.get("enabled") else "❌"
                print(
                    f"     {status} /{path.lstrip('/'):25} "
                    f"→ {entry['page_id']:15} "
                    f"({entry.get('title', entry_slug)})"
                )

        print("=" * 50 + "\n")

    def __repr__(self) -> str:
        total_entries = sum(
            len(g["entries"]) for g in self._data["groups"].values()
        )
        return (
            f"SitemapManager({len(self._data['groups'])} groups, "
            f"{total_entries} entries) 📍"
        )


# ─── Quick Example ──────────────────────────────────────────────

if __name__ == "__main__":
    # Aina-chan's demonstration~♪

    manager = SitemapManager()

    # Add some groups
    manager.add_group("home", "", "Main home page")
    manager.add_group("character", "character", "Character profiles")
    manager.add_group("blog", "blog", "Blog articles")

    # Add entries
    manager.add_entry("home", "", "PAGE_ID_001", "Home Page")
    manager.add_entry("character", "aina", "PAGE_ID_002",
                      "Aina-chan's Page")
    manager.add_entry("character", "anita", "PAGE_ID_003",
                      "Anita's Page")
    manager.add_entry("blog", "hello-world", "PAGE_ID_004",
                      "Hello World Post")

    # Print the sitemap
    manager.print_sitemap()

    # Resolve a path
    page_id = manager.get_page_id_by_path("/character/aina")
    print(f"Path /character/aina → Page ID: {page_id}")

    # Get active routes only
    active = manager.get_active_routes()
    print(f"\nActive routes: {active}")

    # Get tree for navigation
    tree = manager.get_active_routes_tree()
    print(f"\nNavigation tree: {json.dumps(tree, indent=2)}")