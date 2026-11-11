#!/usr/bin/env python3
"""Generate the Snaptrail gallery photos.

These are *synthetic* travel-style images (sky gradient + horizon + a sun/moon
and the destination caption) rendered with Pillow. We generate them rather than
ship real photos so the lab stays self-contained, lightweight and free of any
third-party image licensing.

Run it from the repo root to (re)create the JPGs under ``photos/``:

    python tools/generate_photos.py

The set of photos (filename + caption + palette) is the single source of truth
here; keep ``app/config.py``'s LISTED_PHOTOS in sync with these filenames.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# (filename, caption, top sky colour, bottom sky colour, land colour, sun colour)
PHOTOS = [
    (
        "sunrise-bali.jpg",
        "Sunrise · Bali",
        (255, 178, 102),
        (255, 94, 98),
        (40, 30, 40),
        (255, 240, 200),
    ),
    (
        "tokyo-night.jpg",
        "Night · Tokyo",
        (18, 20, 48),
        (70, 30, 90),
        (10, 10, 20),
        (240, 90, 160),
    ),
    (
        "patagonia-trek.jpg",
        "Trek · Patagonia",
        (120, 180, 210),
        (210, 230, 240),
        (70, 90, 80),
        (255, 255, 255),
    ),
    (
        "santorini-blue.jpg",
        "Caldera · Santorini",
        (90, 150, 220),
        (200, 230, 250),
        (235, 235, 240),
        (255, 250, 230),
    ),
    (
        "sahara-dunes.jpg",
        "Dunes · Sahara",
        (250, 210, 140),
        (230, 150, 80),
        (150, 95, 45),
        (255, 245, 210),
    ),
    (
        "iceland-aurora.jpg",
        "Aurora · Iceland",
        (10, 25, 40),
        (20, 70, 80),
        (15, 20, 30),
        (120, 255, 180),
    ),
]

WIDTH, HEIGHT = 800, 600
OUT_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "photos")


def _vertical_gradient(
    top: tuple[int, int, int], bottom: tuple[int, int, int]
) -> Image.Image:
    """Create a smooth vertical gradient from ``top`` to ``bottom``."""
    base = Image.new("RGB", (1, HEIGHT))
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        base.putpixel(
            (0, y),
            tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )
    return base.resize((WIDTH, HEIGHT))


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Best-effort load of a TrueType font, falling back to the default."""
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _render(spec: tuple) -> Image.Image:
    filename, caption, top, bottom, land, sun = spec
    img = _vertical_gradient(top, bottom)
    draw = ImageDraw.Draw(img, "RGBA")

    # Sun / moon disc.
    cx, cy, r = int(WIDTH * 0.72), int(HEIGHT * 0.3), 70
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sun + (235,))

    # Rolling land / horizon as a couple of overlapping hills.
    horizon = int(HEIGHT * 0.68)
    draw.polygon(
        [
            (0, horizon + 60),
            (WIDTH * 0.35, horizon - 30),
            (WIDTH * 0.7, horizon + 40),
            (WIDTH, horizon - 10),
            (WIDTH, HEIGHT),
            (0, HEIGHT),
        ],
        fill=land + (255,),
    )
    draw.rectangle([0, int(HEIGHT * 0.82), WIDTH, HEIGHT], fill=land + (255,))

    # Soften everything slightly so it reads as a photo, not flat vector art.
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    draw = ImageDraw.Draw(img, "RGBA")

    # Caption with a subtle shadow for legibility over any background.
    font = _load_font(40)
    tx, ty = 40, HEIGHT - 80
    draw.text((tx + 2, ty + 2), caption, font=font, fill=(0, 0, 0, 160))
    draw.text((tx, ty), caption, font=font, fill=(255, 255, 255, 235))

    return img


def main() -> None:
    out = os.path.abspath(OUT_DIR)
    os.makedirs(out, exist_ok=True)
    for spec in PHOTOS:
        img = _render(spec)
        path = os.path.join(out, spec[0])
        img.save(path, "JPEG", quality=85)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
