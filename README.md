# 🏔️ Snaptrail

[![Integration](https://github.com/iv0ks/snaptrail/actions/workflows/integration.yml/badge.svg)](https://github.com/iv0ks/snaptrail/actions/workflows/integration.yml)
[![Release](https://github.com/iv0ks/snaptrail/actions/workflows/release.yml/badge.svg)](https://github.com/iv0ks/snaptrail/actions/workflows/release.yml)
[![Delivery](https://github.com/iv0ks/snaptrail/actions/workflows/delivery.yml/badge.svg)](https://github.com/iv0ks/snaptrail/actions/workflows/delivery.yml)
[![GHCR](https://img.shields.io/badge/ghcr.io-iv0ks%2Fsnaptrail-blue?logo=docker)](https://github.com/iv0ks/snaptrail/pkgs/container/snaptrail)

> **Snaptrail** is a tiny "travel photo gallery" — browse your trip photos and
> open any of them full-size. At least, that's the pitch.

---

## ⚠️ Disclaimer — read this first

**Snaptrail is an intentionally vulnerable application built for security
education.** It contains a deliberate [path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
(CWE-22) flaw so you can practice finding and exploiting it in a safe,
controlled, local environment (for example with [Burp Suite](https://portswigger.net/burp)).

- ✅ Run it **locally**, against `localhost`, on infrastructure you own.
- ❌ Do **not** deploy it on a public/shared server.
- ❌ Do **not** reuse this code in real software.
- ❌ Do **not** use these techniques against systems you don't have explicit
  permission to test. Unauthorized testing is illegal.

This repository is part of a series of educational AppSec labs
(topic: [`appsec-lab`](https://github.com/topics/appsec-lab)).

---

## 🎯 The challenge

Snaptrail serves your photos from a gallery directory. The endpoint always
prepends that directory to the requested filename — a *forced prefix* the
developer believes keeps you inside the gallery. Your goal:

> **Read a file that lives _outside_ the gallery — specifically, capture the
> flag stored in `flag.txt`, one level above the served `photos/` dir.**

The flag has the format `FLAG{...}`.

| | |
|---|---|
| **Vulnerability** | Path Traversal (CWE-22) |
| **Difficulty** | ⭐⭐ Level 2 — forced base-path prefix |
| **Stack** | Python · Flask · gunicorn |
| **Entry point** | `GET /media?name=<filename>` |

> **Target:** capture the flag in `flag.txt`, which lives one level *above* the
> served `photos/` directory.

### Hints

<details>
<summary>Hint 1</summary>
The gallery opens photos by name. What is that name used for on the server
side? Watch the request in Burp.
</details>

<details>
<summary>Hint 2</summary>
The app always prepends a <code>photos/</code> directory to your input. Does
prepending a folder actually stop you from walking <em>out</em> of it?
</details>

<details>
<summary>Hint 3</summary>
Prepending a base path does not neutralize <code>../</code> sequences. The flag
is one directory <em>above</em> <code>photos/</code>.
</details>

A full walkthrough lives in [SOLUTION.md](SOLUTION.md) (spoilers!).

---

## 🗂️ Project layout

```
snaptrail/
├── app/                    # the application package (the bug lives here)
│   ├── main.py             # Flask app factory (resolves paths, error handlers)
│   ├── routes.py           # routes — the vulnerable media endpoint
│   ├── config.py           # static defaults (dir name, listed photos)
│   ├── static/
│   │   └── style.css       # gallery + error page styles (with dark mode)
│   └── templates/
│       ├── gallery.html    # UI (kept out of the Python code)
│       └── error.html      # styled error page
├── photos/                 # the served gallery (the "allowed" directory)
│   ├── sunrise-bali.jpg
│   ├── tokyo-night.jpg
│   └── patagonia-trek.jpg
├── tests/                  # exploit + happy-path tests (pytest)
├── SOLUTION.md             # exploit writeup + the fix (spoilers)
├── .github/workflows/      # integration · delivery · release (via cicd-hub)
├── Dockerfile              # hardened multi-stage image (creates the flag)
├── docker-compose.yml      # Traefik + the app service
├── pyproject.toml          # ruff + black + pytest config, packaging
└── requirements.txt
```

The application code lives in `app/` and reads its photos from `photos/`, just
like a real service would. The target `flag.txt` is **not** in the repo: the
`Dockerfile` writes it to `/app/flag.txt` at build time — one level *above* the
served `photos/` dir — so traversal can reach it while the flag stays out of
version control (and out of the served directory the app is meant to expose).

---

## 🚀 Running the lab

### Option A — Docker Compose

The provided `docker-compose.yml` wires the app behind a [Traefik](https://traefik.io/)
reverse proxy on the external `iv0ks-dev` network (TLS for `snaptrail.iv0ks.dev`).
It mirrors the real deployment. For a quick local run you usually want Option B
or C instead.

```bash
docker network create iv0ks-dev   # once, if it does not exist
docker compose up --build
```

### Option B — Build and run just the image

```bash
docker build -t snaptrail .
docker run --rm -p 5000:5000 --read-only --tmpfs /tmp -e HOME=/tmp snaptrail
```

Or pull the published image from GHCR:

```bash
docker run --rm -p 5000:5000 ghcr.io/iv0ks/snaptrail:latest
```

Then open <http://localhost:5000>.

### Option C — Run directly with Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the app (the `app` package lives at the repo root). Either works:
flask --app app.main run --port 5000
# ...or with auto-reload while developing:
flask --app app.main run --port 5000 --debug
```

Then open <http://localhost:5000>.

> The app finds its data via the `DATA_ROOT` env var, defaulting to the repo
> root (it serves `<DATA_ROOT>/photos/` and the flag is at `<DATA_ROOT>/flag.txt`).
> The flag is **not** committed — it is provisioned at runtime: the Docker image
> bakes it in at build time, and when you run from Python the app seeds
> `flag.txt` on startup if it is missing. Either way the challenge just works.
> Override the value with the `FLAG` env var (or `--build-arg FLAG=...` for
> Docker). The seeded `flag.txt` is gitignored, so it never lands in the repo.

---

## 🧰 About this repo (DevSecOps showcase)

Beyond the vulnerability, this repo is also a template for shipping a small
service with sane engineering practices:

- **Conventional Commits** enforced via **commitlint** (pre-commit hook).
- **pre-commit** suite: `ruff`, `black`, `gitleaks` (secret scanning),
  `hadolint` (Dockerfile lint), whitespace/EOF fixers.
- **Centralized CI/CD** via reusable workflows in
  [`iv0ks/cicd-hub`](https://github.com/iv0ks/cicd-hub):
  - **Integration** (`integration.yml`): secret scan → lint → tests on every PR.
  - **Delivery** (`delivery.yml`): build & push the image to **GHCR**, then
    scan it, on every tag.
  - **Release** (`release.yml`): automated SemVer releases and changelog from
    commits via **release-please**.
- **Dependabot**: daily updates for pip, Docker and GitHub Actions.
- **Hardened container**: multi-stage build, non-root user, read-only root
  filesystem, dropped capabilities.

> 💡 **Teaching note:** image/dependency scanners (e.g. Trivy) look for *known
> CVEs in dependencies and the base image*. They will **not** flag Snaptrail's
> path traversal, because that is a **business-logic** flaw in our own code,
> not a vulnerable dependency. Catching that class of bug needs SAST / manual
> review / DAST — which is exactly what you're practicing here. Different
> tools, different coverage.

Set up the hooks locally with:

```bash
pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type commit-msg
pre-commit run --all-files
```

### Running the tests

```bash
pip install pytest
pytest
```

The suite documents the behaviour executably: the intended photo opens, the
styled error pages render, and `../flag.txt` really does escape `photos/` and
read the flag — so if someone "fixes" the bug, the exploit test turns red.

---

## 📄 License

[MIT](LICENSE) — see also [SECURITY.md](SECURITY.md).
