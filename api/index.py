import os
import sys

# Add root directory and expense_tracker to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tracker_dir = os.path.join(root_dir, "expense_tracker")

if tracker_dir not in sys.path:
    sys.path.insert(0, tracker_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from expense_tracker.app import app

class VercelWSGIMiddleware:
    """
    Vercel rewrites all routes to /api/index.py.
    This middleware restores the original requested path (e.g. /, /login, /export/pdf)
    from HTTP_X_MATCHED_PATH or REQUEST_URI so Flask matches routes correctly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get("HTTP_X_MATCHED_PATH")
        path_info = environ.get("PATH_INFO", "")

        if path_info in ["/api/index.py", "/api/index", ""]:
            if matched_path:
                environ["PATH_INFO"] = matched_path
            elif environ.get("REQUEST_URI"):
                environ["PATH_INFO"] = environ["REQUEST_URI"].split("?")[0]
            else:
                environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
