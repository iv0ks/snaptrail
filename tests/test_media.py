"""Tests for Snaptrail's media endpoint.

These document the app's behaviour executably:

* the *intended* path (opening a listed photo) works, and
* the *path traversal* (CWE-22, level 2 — forced prefix) actually escapes the
  gallery and reads the flag.

The exploit test is deliberately asserting that the vulnerability is present —
if someone "fixes" the bug, this test turns red and flags that the lab no
longer teaches what it claims to.

The flag does NOT live in the repo (it is created inside the Docker image at
build time). So the fixture builds a throwaway data root that mirrors the
runtime layout — ``<root>/photos/`` for served files and ``<root>/flag.txt`` as
the traversal target — and points the app at it via the ``DATA_ROOT`` env var.
Because the factory reads DATA_ROOT at call time, this needs no module reloads.
"""

from __future__ import annotations

import pytest

from app.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Mirror the runtime layout inside a temp dir.
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    (photos_dir / "sunrise-bali.jpg").write_text("fake-jpeg-bytes-sunrise\n")
    (photos_dir / "tokyo-night.jpg").write_text("fake-jpeg-bytes-tokyo\n")
    (photos_dir / "patagonia-trek.jpg").write_text("fake-jpeg-bytes-patagonia\n")
    (tmp_path / "flag.txt").write_text("FLAG{P4TH_TR4V3RS4L_L3V3L_2}\n")

    # Point the factory at the temp root (read at create_app() time).
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))

    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_gallery_lists_photos(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"sunrise-bali.jpg" in resp.data


def test_open_served_photo(client):
    """The intended, happy-path opening of a listed photo works."""
    resp = client.get("/media?name=sunrise-bali.jpg")
    assert resp.status_code == 200
    assert b"fake-jpeg-bytes-sunrise" in resp.data


def test_path_traversal_reads_the_flag(client):
    """CWE-22 (level 2): `../flag.txt` escapes the forced prefix and reads the flag."""
    resp = client.get("/media?name=../flag.txt")
    assert resp.status_code == 200
    assert b"FLAG{" in resp.data


def test_missing_name_returns_styled_400(client):
    resp = client.get("/media")
    assert resp.status_code == 400
    assert b"Snaptrail" in resp.data  # styled error page, not raw Flask error


def test_unknown_name_returns_styled_404(client):
    resp = client.get("/media?name=does-not-exist.jpg")
    assert resp.status_code == 404
    assert b"Snaptrail" in resp.data


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.data == b"ok"
