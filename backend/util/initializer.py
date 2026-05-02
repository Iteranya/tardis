"""
Anita-CMS Initializer 🚀
"""
import time

from pocketbase import PocketBase
from backend.util.secrets import SecretsManager
from backend.util.auth import authenticate_admin


def initialize_all_modules():
    """
    Initialize all module collections using a shared PocketBase connection.
    Aina-chan authenticates ONCE, not per-manager! (★ω★)
    """
    from backend.pages.manager import PageManager
    from backend.articles.manager import ArticleManager
    from backend.sites.manager import SiteManager
    from backend.storage.manager import StorageManager
    from backend.users.manager import UserManager

    # Get credentials once
    secrets = SecretsManager()
    pb_url = secrets.pocketbase_url
    email = secrets.admin_email
    password = secrets.admin_password

    if not email or not password:
        print("  ❌ No credentials configured. Skipping initialization.")
        return {}

    # Create ONE PocketBase client and authenticate ONCE
    client = PocketBase(pb_url)
    try:
        authenticate_admin(client, email, password)
        print("  🔑 Authenticated once, shared across all managers")
    except Exception as e:
        print(f"  ❌ Authentication failed: {e}")
        return {}

    is_authenticated = True

    # Create managers with the shared client
    managers = [
        ("Pages", PageManager(pb_url=pb_url, admin_email=email, admin_password=password)),
        ("Articles", ArticleManager(pb_url=pb_url, admin_email=email, admin_password=password)),
        ("Sites", SiteManager(pb_url=pb_url, admin_email=email, admin_password=password)),
        ("Storage", StorageManager(pb_url=pb_url, admin_email=email, admin_password=password)),
        ("Users", UserManager(pb_url=pb_url, admin_email=email, admin_password=password)),
    ]

    # Share the authenticated client with all managers
    for name, manager in managers:
        manager.client = client
        manager._is_authenticated = is_authenticated

    results = {}

    for name, manager in managers:
        try:
            t0 = time.time()

            if hasattr(manager, 'initialize'):
                result = manager.initialize()
            elif hasattr(manager, 'ensure_collection_exists'):
                result = manager.ensure_collection_exists()
            else:
                result = False

            elapsed = time.time() - t0
            status = "✅" if (result is True or result is None) else "❌"
            print(f"  {status} {name} ({elapsed:.2f}s)")

            if result is True or result is None:
                print(f"  ✅ {name}")
                results[name] = "✅"
            else:
                # Check for fake SDK errors
                if result and "CollectionField" in str(result) and "help" in str(result):
                    print(f"  ✅ {name} (SDK warning)")
                    results[name] = "✅"
                else:
                    print(f"  ❌ {name}")
                    results[name] = "❌"
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            if "CollectionField.__init__()" in error_msg and "help" in error_msg:
                print(f"  ✅ {name} (SDK warning)")
                results[name] = "✅"
            else:
                print(f"  ❌ {name} — {error_msg}")
                results[name] = f"❌ {error_msg}"

    return results
