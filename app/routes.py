"""Snaptrail HTTP routes.

The media endpoint is intentionally vulnerable. The developer *thinks* that
always prepending the gallery directory to the requested name keeps requests
inside the gallery (a "forced prefix"). But prepending a base path does not
stop ``../`` sequences from walking back out of it, so values like
``../flag.txt`` or ``../../etc/passwd`` still escape. This is a path traversal
behind a forced prefix (CWE-22, level 2) and is the whole point of this lab.

    GET /media?name=sunrise-bali.jpg  -> serves photos/sunrise-bali.jpg
    GET /media?name=../flag.txt       -> escapes the gallery (the flag)

Paths come from ``current_app.config`` (set by the factory), so the routes
don't read the environment or import mutable globals.

Do NOT reuse this pattern in real software. See README.md for the disclaimer.
"""

from __future__ import annotations

import os

from flask import (
    Blueprint,
    Response,
    current_app,
    render_template,
    request,
    send_file,
)

bp = Blueprint("snaptrail", __name__)


@bp.get("/")
def gallery() -> str:
    """Render the gallery dashboard listing the user's photos."""
    photos = current_app.config["LISTED_PHOTOS"]
    return render_template("gallery.html", photos=photos)


@bp.get("/media")
def media() -> Response:
    """Serve a photo from the gallery.

    VULNERABLE BY DESIGN (level 2 — forced prefix): the gallery directory is
    always prepended to the ``name`` parameter, but the result is never checked
    to stay inside it. ``os.path.join`` also resolves an absolute ``name`` by
    discarding the prefix, and keeps any ``..`` components, so the request can
    walk out of the gallery (CWE-22).
    """
    name = request.args.get("name", "")
    if not name:
        return render_error(400, "Missing 'name' query parameter.")

    gallery_dir = current_app.config["GALLERY_DIR"]

    # --- The vulnerable line -------------------------------------------------
    # The "forced prefix": gallery_dir is always prepended. The developer
    # assumes this confines the request to the gallery, but os.path.join keeps
    # '..' components (and would honour an absolute name), so the boundary is
    # never actually enforced.
    target_path = os.path.join(gallery_dir, name)
    # -------------------------------------------------------------------------

    if not os.path.isfile(target_path):
        return render_error(404, f"Photo not found: {name}")

    return send_file(target_path, as_attachment=False)


@bp.get("/healthz")
def healthz() -> Response:
    """Liveness probe used by Docker's HEALTHCHECK."""
    return Response("ok", mimetype="text/plain")


def render_error(status: int, message: str) -> Response:
    """Render the styled error page with the given status and message."""
    html = render_template("error.html", status=status, message=message)
    return Response(html, status=status, mimetype="text/html")
