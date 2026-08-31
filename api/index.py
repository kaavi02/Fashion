import sys
from pathlib import Path

# Ensure the root directory is on the Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app as _base_app

# ASGI Wrapper to guarantee paths and forwarded headers are preserved cleanly
class VercelApp:
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            # If Vercel passed an original path in x-forwarded-uri, ensure scope matches
            forwarded_uri = headers.get(b"x-forwarded-uri")
            if forwarded_uri:
                decoded = forwarded_uri.decode("latin1").split("?")[0]
                if decoded:
                    scope["path"] = decoded
            elif scope.get("path") in ("/api/index.py", "/api/index"):
                # Rewrote to entrypoint filename, default to root
                scope["path"] = "/"

        await self.asgi_app(scope, receive, send)

app = VercelApp(_base_app)
