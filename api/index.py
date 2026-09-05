import os
import sys
import urllib.parse
import re

# Add root directory and expense_tracker module to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tracker_dir = os.path.join(root_dir, "expense_tracker")

if tracker_dir not in sys.path:
    sys.path.insert(0, tracker_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from expense_tracker.app import app

class VercelWSGIMiddleware:
    """
    Ensures that rewritten Vercel requests correctly map to Flask routes.
    Extracts the original request path from __path__ query param or headers,
    cleans query string, and avoids infinite redirect loops.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        parsed_qs = urllib.parse.parse_qs(query_string, keep_blank_values=True)

        target_path = None
        if "__path__" in parsed_qs:
            target_path = parsed_qs.pop("__path__", [""])[0]
            environ["QUERY_STRING"] = urllib.parse.urlencode(parsed_qs, doseq=True)

        if not target_path:
            # Fallback to headers or REQUEST_URI
            raw = environ.get("HTTP_X_FORWARDED_URI") or environ.get("REQUEST_URI") or environ.get("PATH_INFO", "")
            target_path = raw.split("?")[0] if raw else "/"

        # Normalize path
        if not target_path.startswith("/"):
            target_path = "/" + target_path
        target_path = re.sub(r"/+", "/", target_path)

        # If path ended up being the serverless script itself, route to root
        if target_path in ["/api/index.py", "/api/index"]:
            target_path = "/"

        environ["PATH_INFO"] = target_path
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
