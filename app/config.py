"""Snaptrail configuration — static defaults.

These are pure constants. The actual runtime paths (which depend on the
``DATA_ROOT`` env var) are resolved by the application factory in
``app.main.create_app`` and stored on ``app.config``, so nothing here reads the
environment at import time. That keeps the app easy to test: each ``create_app``
call can be pointed at a different data root.

Runtime layout (resolved in the factory):

    <data_root>/           <- DATA_ROOT     (holds flag.txt, the target)
    <data_root>/photos/    <- GALLERY_DIR   (the served photo gallery)
"""

from __future__ import annotations

import os

# Repo root is one level above the app/ package. Used as the DATA_ROOT default.
DEFAULT_DATA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Name of the sub-directory (under DATA_ROOT) the app serves photos from. This
# is the "forced prefix": the endpoint always prepends it to the requested
# name. The bug is that it is prepended but never enforced as a boundary.
GALLERY_DIRNAME = "photos"

# The challenge flag. It is the *target* of the path traversal and lives at
# <DATA_ROOT>/flag.txt (one level above the served photos/). It is intentionally
# not committed to the repo; the app seeds it on startup if missing (and the
# Docker image also writes it at build time). Override via the FLAG env var.
FLAG_FILENAME = "flag.txt"
DEFAULT_FLAG = "FLAG{P4TH_TR4V3RS4L_L3V3L_2}"

# Photos shown on the gallery so the app behaves like a real product.
LISTED_PHOTOS = [
    "sunrise-bali.jpg",
    "tokyo-night.jpg",
    "patagonia-trek.jpg",
]
