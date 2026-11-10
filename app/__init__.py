"""Snaptrail app package — intentionally vulnerable path traversal lab (Flask)."""

from app.main import app, create_app

__all__ = ["app", "create_app"]
