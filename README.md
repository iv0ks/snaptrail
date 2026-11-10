# Snaptrail

[![GHCR](https://img.shields.io/badge/ghcr.io-iv0ks%2Fsnaptrail-blue?logo=docker)](https://github.com/iv0ks/snaptrail/pkgs/container/snaptrail)


**Snaptrail is an intentionally vulnerable application built for security education.** It contains a deliberate [path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
(CWE-22) flaw — hidden behind a forced base-path prefix — so you can practice finding and exploiting it in a safe and controlled environment.

<br>

## 🗂️ Project layout

The repository is organised so the vulnerable code is easy to find and reason
about. Three areas, clearly separated: the **application** itself in `app/`
(a small Flask app split into factory, routes and config), the **served data**
in `photos/` (the directory the app is *meant* to expose), and the **tooling**
around it (Docker, CI/CD, linters) that turns the lab into a production-shaped
project. The challenge flag is deliberately kept *out* of both the repo and the
served directory — see the note under the tree.

```
snaptrail/
├── app/                    # the application package (the bug lives here)
│   ├── main.py             # Flask app factory (resolves paths, error handlers)
│   ├── routes.py           # routes — the vulnerable media endpoint
│   ├── config.py           # static defaults (dir name, listed photos)
│   ├── static/
│   │   └── style.css       # gallery + error page styles
│   └── templates/
│       ├── gallery.html    # UI (kept out of the Python code)
│       └── error.html      # styled error page
├── photos/                 # the served gallery (the "allowed" directory)
│   ├── sunrise-bali.jpg
│   ├── tokyo-night.jpg
│   └── patagonia-trek.jpg
├── tests/                  # exploit + happy-path tests (pytest)
├── tools/traefik/          # reverse-proxy config (static + dynamic routing)
├── SOLUTION.md             # exploit writeup + the fix (spoilers)
├── SECURITY.md             # security policy (it's a lab — read before reporting)
├── .github/workflows/      # integration · delivery · security · release
├── Dockerfile              # hardened multi-stage image (creates the flag)
├── docker-compose.yml      # snaptrail + traefik stack
├── .env.example            # Traefik ACME credentials template (copy to .env)
├── pyproject.toml          # ruff + black + pytest config, packaging
└── requirements.txt
```

The application code lives in `app/` and reads its photos from `photos/`, just like a real service would. The target `flag.txt` is **not** in the repo: the `Dockerfile` writes it to `/app/flag.txt` at build time.

<br>

## 🚀 The Lab

The lab ships as a Docker Compose stack with two services:

- **`snaptrail`** — the app itself, published on port `5000`.
- **`traefik`** — a reverse proxy that serves the app over HTTPS on a real
  hostname. It is optional: you only need it for the domain-based access.

Because the stack attaches to an **external** Docker network (`iv0ks-dev`),
create it once before the first run:

```bash
docker network create iv0ks-dev
```

#### Option A — just the app (quickest)

Start only the `snaptrail` service (Compose skips `traefik` when you name a
service explicitly):

```bash
docker compose up -d snaptrail
```

The app is now reachable directly at:

- **<http://localhost:5000>**

That is all you need to start playing with Burp Suite.

#### Option B — full stack with Traefik (HTTPS + hostname)

Bring up both services to also expose the app through Traefik with TLS:

```bash
docker compose up -d
```

Now the *same* app is reachable two ways at once:

- **<http://localhost:5000>** — direct, no TLS (handy for quick testing).
- **<https://snaptrail.iv0ks.dev>** — proxied by Traefik with a real certificate.

Traefik routing is defined in `tools/traefik/` (static config in `traefik.yml`,
the `snaptrail` router in `dynamic.yml`). TLS uses the ACME DNS-01 challenge via
Namecheap, so Traefik needs those API credentials — copy `.env.example` to
`.env` and fill them in (the `.env` file is gitignored). The dashboard is at
`https://traefik.iv0ks.dev`.

> The `snaptrail.iv0ks.dev` hostname must resolve to the host running the stack.
> For purely local experiments, Option A (localhost) is simpler and needs no
> DNS or certificates.

#### Running without cloning (prebuilt image)

The published image on GHCR runs standalone, no Compose needed:

```bash
docker run --rm -p 5000:5000 ghcr.io/iv0ks/snaptrail:latest
```

Then open <http://localhost:5000>.

<br>

## 🎯 The Challenge

Snaptrail serves your photos from a gallery directory. The endpoint always
prepends that directory to the requested filename — a *forced prefix* the
developer believes keeps you inside the gallery. Your goal:

> **Read a file that lives _outside_ the gallery — specifically, capture the
> flag stored in `flag.txt`.**

The flag has the format `FLAG{...}`. A full walkthrough lives in [SOLUTION.md](SOLUTION.md).
