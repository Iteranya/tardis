from pocketbase import PocketBase
from backend.util.secrets import get_secrets


class DashboardManager:
    def __init__(self, token: str):
        self.token = token
        secrets = get_secrets()
        self.pb_url = secrets.pocketbase_url
        self.client = PocketBase(self.pb_url)
        self.client.auth_store.save(token)

    def get_total(self, collection: str) -> int:
        try:
            result = self.client.collection(collection).get_list(
                page=1,
                per_page=1,
                query_params={"skipTotal": False}
            )
            return result.total_items
        except Exception as e:
            print(f"📊 [DashboardManager] Failed to count '{collection}': {e}")
            return 0

    def get_all_stats(self) -> dict:
        return {
            "pages": self.get_total("sys_pages"),
            "articles": self.get_total("sys_articles"),
            "sites": self.get_total("sys_sites"),
            "storage": self.get_total("sys_storage"),
            "users": self.get_total("users"),
        }
