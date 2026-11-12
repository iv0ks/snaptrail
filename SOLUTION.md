# Snaptrail: Solution / Walkthrough

![CWE-22](https://img.shields.io/badge/CWE--22-Path%20Traversal-red?style=flat-square)
![Python](https://img.shields.io/badge/Python-Flask-blue?style=flat-square&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Lab-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

**Snaptrail is an intentionally vulnerable application built for security education.** It contains a deliberate [path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
(CWE-22) flaw — hidden behind a forced base-path prefix — so you can practice finding and exploiting it in a safe and controlled environment.

<br>

> [!WARNING]
> This page gives away the payload and the flag. If you want to solve it yourself, start with the non-spoiler **[Learning Guide](GUIDE.md)** and come back here to check your work.

<br>

## 📚 What you'll get from this page

The [Learning Guide](GUIDE.md) covers *what* path traversal is and *how* to
approach the lab. This page is the spoiler half: the confirmed exploit, the
flag, and — most importantly — the **why** behind the bug and its fix. By the
end you should be able to:

- Read a snippet of file-serving code and point to the exact vulnerable line.
- Explain why a "forced prefix" is not a security boundary.
- Explain **why** each fix works — and why some "obvious" fixes don't.

> **One-line recap** (full version in the [GUIDE](GUIDE.md)): path traversal
> happens when an app builds a file path from user input and trusts it to stay
> inside the intended folder. A forced `photos/` prefix fixes where the path
> *starts*, not where it *ends* — `../` still walks out.

If you only want the payload, jump to [Exploitation](#-exploitation) — but the
real value is in the *why*.

<br>

## 🐛 The vulnerability

The `app/routes.py` builds the file path like this:

```python
name = request.args.get("name", "")            # attacker controls this
gallery_dir = current_app.config["GALLERY_DIR"]

target_path = os.path.join(gallery_dir, name)      # the "forced prefix"

if not os.path.isfile(target_path):
    return render_error(404, f"Photo not found: {name}")

return send_file(target_path, as_attachment=False)
```

Walk through it the way the computer does:

1. `name` comes **straight from the query string** — fully attacker-controlled.
2. `os.path.join(gallery_dir, name)` glues the gallery path in front of it. The
   developer treats this prefix as a fence. It isn't: `os.path.join` keeps `..`
   segments intact, so `name="../flag.txt"` resolves *above* the gallery.
3. Worse, `os.path.join` has a quirk — if `name` is an **absolute** path
   (`/etc/passwd`), it **discards** `gallery_dir` completely and returns the
   absolute path. The "forced" prefix isn't even always applied.
4. The code checks the file *exists* (`isfile`) but never that it lives
   **inside** `gallery_dir`.

The missing step is a **boundary check** on the *resolved* path. Prepending a
base directory feels protective, but it only controls the starting point — the
`..` in the user's input does the rest.

> **Why does this look safe?** Because "we always serve from `photos/`" is a
> sentence that sounds like containment. The code *does* always mention
> `photos/` — it just doesn't *enforce* staying there.

<br>

## 💥 Exploitation

**The intended request** — what the app expects:

```
GET /media?name=sunrise-bali.jpg
```

Resolves to `photos/sunrise-bali.jpg`. Working as designed.

**The exploit** — walk back out of the forced `photos/` prefix to read the flag
one level up:

```
GET /media?name=../flag.txt
```

`os.path.join("photos", "../flag.txt")` resolves to `flag.txt` at the parent
level — outside the gallery. Let's send it.

With `curl`:

```bash
curl --path-as-is "http://localhost:5000/media?name=../flag.txt"
```

> **Why `--path-as-is`?** By default curl normalises `../` away *before* the
> request leaves your machine, so the server never sees the traversal.
> `--path-as-is` sends your path byte-for-byte. Browsers and some proxies do the
> same normalisation — a common reason a payload "works in Repeater but not in
> the browser."

Expected output:

```
FLAG{SNAPTRAIL_OFF_THE_TRAIL}
```

> **Where does the flag come from?** It is **not** in the repo — it is baked into
> the Docker image at build time at `/app/flag.txt`, one level above `photos/`
> (see the `Dockerfile`). You have to actually exploit the traversal against the
> running container to read it.

<br>

## 🚀 Going further

Two directions worth trying:

```
GET /media?name=../../../../etc/passwd    # keep climbing to the FS root
GET /media?name=/etc/passwd               # absolute path: the prefix is discarded
```

The second is the eye-opener specific to this level: because `os.path.join`
drops the base directory when handed an absolute path, the "forced prefix"
evaporates entirely.

> Inside the hardened container these read the *container's* files, not your
> host's, and the app runs as a non-root user — the blast radius is deliberately
> small. That containment is exactly why we run labs in Docker.

<br>

## 🛠️ Doing it in Burp Suite

Prefer a proxy-driven workflow? This mirrors a real engagement:

1. Proxy your browser through Burp and load <http://localhost:5000>.
2. Click **Open** on any photo — capture the request in **Proxy > HTTP history**.
   Notice the filename lands in `?name=`.
3. Send it to **Repeater** and re-send the original value to get a **baseline**.
4. Change `name` to `../flag.txt` and send. Compare against the baseline — a
   different body with the flag confirms the escape.
5. (Optional) Fuzz with **Intruder** using a path-traversal wordlist (e.g. from
   [SecLists](https://github.com/danielmiessler/SecLists)), and try an absolute
   path to see the prefix get discarded.

> If a payload that works in `curl --path-as-is` fails in Repeater, Burp's
> URL-encoding/normalisation is usually the culprit — inspect the raw request.

<br>

## 🛡️ The fix

Prepending a base directory is not a boundary. **Resolve** the final path to its
canonical form, then **verify** it still lives inside the allowed base:

```python
import os
from flask import abort, send_file

def safe_path(base_dir: str, user_supplied: str) -> str:
    # realpath() collapses '..' and resolves symlinks, giving the true
    # destination the OS would actually open.
    full = os.path.realpath(os.path.join(base_dir, user_supplied))
    base = os.path.realpath(base_dir)

    # The boundary check: the resolved path must sit inside base_dir.
    if os.path.commonpath([full, base]) != base:
        abort(403)
    return full
```

Why this works: `realpath` collapses the `..` *before* the check, so you
validate the path the OS will actually open; and because an absolute input
resolves to somewhere outside `base`, the `commonpath` check rejects it too.

### ⚠️ Tempting fixes that *don't* work

These are the traps specific to a forced-prefix design:

- **"The prefix is enough."** This is the bug itself. Prepending `photos/`
  controls where the path *starts*, not where `..` takes it. Containment must be
  checked on the **resolved** path, not assumed from the prefix.
- **Rejecting only an absolute `name`.** Closing the absolute-path quirk is good,
  but a relative `../flag.txt` still escapes. You need the boundary check too.
- **Stripping `..` from the string** (`name.replace("..", "")`). A single-pass
  strip is bypassable — `....//` collapses *back* into `../` after the replace.
  You'll exploit exactly this in **[deskmint (Level 3)](https://github.com/iv0ks/deskmint)**.

> Series thread: **[fetchly (Level 1)](https://github.com/iv0ks/fetchly)** had
> *no* defence; Snaptrail adds a prefix that only *looks* like one. Next,
> deskmint tries to *filter* `..` — and fails differently.

### ✅ Even better: don't build paths from user input at all

- **Opaque IDs.** Serve photos by a server-side ID (`/media?id=42`) mapped to a
  real path. The user never names a file, so there's nothing to traverse.
- **Allow-list.** Accept only names you explicitly know
  (`if name not in LISTED_PHOTOS: abort(404)`).
- **Use a vetted helper.** Flask's
  [`send_from_directory`](https://flask.palletsprojects.com/en/latest/api/#flask.send_from_directory)
  performs the safe-join boundary check for you.

<br>

## 🎓 Key takeaways

If you remember five things from this lab, make it these:

1. **A base-path prefix is not a boundary.** It sets the start of the path, not
   its end.
2. **`os.path.join` keeps `..` — and drops the base on an absolute input.** It's
   string glue with sharp edges, not a security control.
3. **Resolve, then check.** Canonicalise with `realpath` *before* validating,
   and fail closed if the result escapes the base directory.
4. **Blacklists lose.** Prefer allow-lists or opaque IDs over filtering bad
   strings — you'll see string-filtering fall apart from Level 3 onward.
5. **Defence in depth matters.** Non-root + container didn't *fix* the bug, but
   it kept the blast radius small.

That's Level 2 — a forced prefix that only looks like a fence. Head back to the
**[Learning Guide](GUIDE.md)** for the method, or the **[README](README.md)** for
the lab setup.
