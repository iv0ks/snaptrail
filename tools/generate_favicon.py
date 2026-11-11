#!/usr/bin/env python3
"""Generate the Snaptrail favicon.

A small compass mark (disc + four-point needle) in the app's teal/orange
palette, rendered with Pillow so it stays reproducible and matches the brand.
It is a *static asset* served by Flask from ``app/static/`` — never through the
vulnerable ``/media`` endpoint.

Run from the repo root:

    python tools/generate_favicon.py

Writes ``app/static/favicon.png`` (base 512 px, also downscaled to 32 px).
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

TEAL = (15, 118, 110, 255)
TEAL_DARK = (11, 43, 39, 255)
ORANGE = (234, 115, 23, 255)
WHITE = (255, 255, 255, 255)

SIZE = 512
STATIC_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "app", "static")


def _render() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded teal background tile.
    draw.rounded_rectangle([0, 0, SIZE, SIZE], radius=int(SIZE * 0.22), fill=TEAL)

    # Compass dial.
    cx = cy = SIZE // 2
    r = int(SIZE * 0.34)
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=TEAL_DARK, outline=WHITE, width=10
    )

    # Four-point compass needle: orange (north) + white (south).
    tip = int(r * 0.82)
    waist = int(r * 0.16)
    north = [(cx, cy - tip), (cx + waist, cy), (cx - waist, cy)]
    south = [(cx, cy + tip), (cx + waist, cy), (cx - waist, cy)]
    draw.polygon(north, fill=ORANGE)
    draw.polygon(south, fill=WHITE)

    # Center hub.
    hub = int(r * 0.12)
    draw.ellipse([cx - hub, cy - hub, cx + hub, cy + hub], fill=WHITE)

    return img


def main() -> None:
    out = os.path.abspath(STATIC_DIR)
    os.makedirs(out, exist_ok=True)
    base = _render()

    big = os.path.join(out, "favicon.png")
    base.save(big, "PNG")
    print(f"wrote {big}")

    small_path = os.path.join(out, "favicon-32.png")
    base.resize((32, 32), Image.LANCZOS).save(small_path, "PNG")
    print(f"wrote {small_path}")


if __name__ == "__main__":
    main()
