"""
Aina-chan's PocketBase shared utilities! (◕‿◕✿)

Helpers for collection existence checks and field manipulation
that work with PocketBase v0.23+.
"""

from typing import Optional


def collection_exists(client, collection_name: str) -> bool:
    """
    Check if a collection exists by name.

    PocketBase's `get_one()` expects an ID (like 'pbc_xxx'),
    not a name. So we use `get_list()` with a filter instead.

    Args:
        client: PocketBase client instance
        collection_name: The collection name to check (e.g., "pages")

    Returns:
        True if the collection exists
    """
    try:
        result = client.collections.get_list(
            query_params={
                "filter": f'name = "{collection_name}"',
                "perPage": 1,
            },
        )
        items = result.get("items", [])
        return len(items) > 0
    except Exception:
        return False


def get_collection_by_name(client, collection_name: str) -> Optional[dict]:
    """
    Get a collection by its name.

    Returns:
        The collection dict, or None if not found.
    """
    try:
        result = client.collections.get_list(
            query_params={
                "filter": f'name = "{collection_name}"',
                "perPage": 1,
            },
        )
        items = result.get("items", [])
        return items[0] if items else None
    except Exception:
        return None


def sanitize_fields(fields: list) -> list:
    """
    Remove unknown keys from field definitions that the Python SDK
    might not understand (like 'help' in PocketBase v0.23+).

    Only keeps keys that the SDK's CollectionField constructor accepts.
    """
    allowed_keys = {
        "id", "name", "type", "required", "min", "max", "pattern",
        "noDecimal", "values", "maxSelect", "collectionId",
        "cascadeDelete", "maxSize", "mimeTypes", "onCreate", "onUpdate",
    }

    sanitized = []
    for field in fields:
        clean = {k: v for k, v in field.items() if k in allowed_keys}
        sanitized.append(clean)

    return sanitized
