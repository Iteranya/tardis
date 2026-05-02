import time
from pocketbase import PocketBase
from backend.util.secrets import SecretsManager
from backend.util.auth import authenticate_admin


def initialize_all_modules():
    """
    Initialize all module collections with a single PocketBase connection.

    Returns:
        dict: Results per module with '✅' or error message.
        Also sets secrets.json "initialized" = True if all succeeded.
    """
    secrets = SecretsManager()
    pb_url = secrets.pocketbase_url
    email = secrets.admin_email
    password = secrets.admin_password

    # Early exit if no credentials
    if not email or not password:
        print("  ❌ No credentials configured. Skipping initialization.")
        return {}

    # Authenticate once
    client = PocketBase(pb_url)
    try:
        authenticate_admin(client, email, password)
        print("  🔑 Authenticated once, shared across all managers")
    except Exception as e:
        print(f"  ❌ Authentication failed: {e}")
        return {}

    # Create managers with shared client and auth
    from backend.pages.manager import PageManager
    from backend.articles.manager import ArticleManager
    from backend.sites.manager import SiteManager
    from backend.storage.manager import StorageManager
    from backend.users.manager import UserManager

    managers = [
        ("Pages", PageManager(pb_url, email, password)),
        ("Articles", ArticleManager(pb_url, email, password)),
        ("Sites", SiteManager(pb_url, email, password)),
        ("Storage", StorageManager(pb_url, email, password)),
        ("Users", UserManager(pb_url, email, password)),
    ]

    # Inject the already-authenticated client
    for _, mgr in managers:
        mgr.client = client
        mgr._is_authenticated = True

    results = {}

    for name, mgr in managers:
        try:
            t0 = time.time()
            # Prefer the consistent "initialize" method, fallback to old name
            init_method = getattr(mgr, 'initialize', None) or getattr(mgr, 'ensure_collection_exists', None)
            result = init_method() if init_method else False
            elapsed = time.time() - t0

            # Check for PocketBase SDK false errors (e.g. "help" field)
            if isinstance(result, Exception):
                if "help" in str(result):
                    result = True  # SDK warning, treat as success

            status = "✅" if result else "❌"
            print(f"  {status} {name} ({elapsed:.2f}s)")
            results[name] = status if result else "❌ Failed"

        except Exception as e:
            msg = str(e).split('\n')[0]
            if "help" in msg:
                print(f"  ✅ {name} (SDK warning)")
                results[name] = "✅"
            else:
                print(f"  ❌ {name} — {msg}")
                results[name] = f"❌ {msg}"

    # Mark as fully initialized if all succeeded
    if all(v == "✅" for v in results.values()):
        secrets.set("initialized", True, save=True)
        print("  ✅ Initialization complete – marked as ready")
    else:
        print("  ⚠️ Some modules failed – setup still required")

    return results
