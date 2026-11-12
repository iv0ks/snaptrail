# Snaptrail: Learning Guide

![CWE-22](https://img.shields.io/badge/CWE--22-Path%20Traversal-red?style=flat-square)
![Python](https://img.shields.io/badge/Python-Flask-blue?style=flat-square&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Lab-Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

**Snaptrail is an intentionally vulnerable application built for security education.** It contains a deliberate [path traversal](https://owasp.org/www-community/attacks/Path_Traversal)
(CWE-22) flaw — hidden behind a forced base-path prefix — so you can practice finding and exploiting it in a safe and controlled environment.

<br>

> [!TIP]
> A guided, **non-spoiler** path to solving this lab. It teaches the *method*, not the answer — the exact winning payload and the flag stay in [SOLUTION.md](SOLUTION.md).

<br>

## 🧬 What path traversal is

Here is the whole idea in one sentence:

> **Path traversal happens when an app builds a file path out of user input and
> then trusts that path to stay where it's supposed to.**

A web app usually wants to serve files from *one* folder — here, `photos/`. The
intended deal is: "give me a filename, I'll give you that image *from this
folder*." The catch is that the folder boundary is a **convention**, not a
**rule** the code enforces. Filesystems understand `..` as "go up one level", so
a filename like `../something.txt` is a perfectly valid instruction to leave the
folder. If nobody checks for it, the app obeys.

Think of `photos/` as a room and the filename as directions. "`sunrise-bali.jpg`"
means "the sunrise photo in this room." "`../something`" means "step out the
door, then grab a file in the hallway." The app was only ever meant to serve
things *in the room* — but it never locked the door.

That "filename → file read" shape is the **sink** you're training your eye to
spot. Once you can recognise it on sight, you can find this bug in seconds.

> Want the deeper background — history, variants, encoding tricks, and the full
> manual-testing workflow with **Burp Suite** and **OWASP ZAP**? Read the shared
> **[Path Traversal field guide](https://github.com/iv0ks/appsec-labs/blob/main/docs/path-traversal.md)**.
> This lab is a hands-on application of it.

<br>

## 🎓 What this level teaches

**Level 2 — a forced base-path prefix.** Snaptrail always prepends the gallery
directory to whatever filename you request. The developer believes that
"always starting from `photos/`" keeps every request inside the gallery. This
is the first *apparent* defence of the series — and the lesson is that
prepending a base directory does nothing on its own: the join still honours
`..` components (and would even honour an absolute path, discarding the prefix
entirely).

- **Entry point:** `GET /media?name=<name>`
- **The broken defence:** a forced `photos/` prefix, with no boundary check on
  the resolved path.
- **Served directory:** `photos/` · **target:** a file one level above it.

## 🪧 How to approach it

1. Open a photo through your proxy and capture the request carrying `name`.
2. Send it to Repeater / Request Editor and re-send the known-good value to get
   your **baseline** response — the thing you'll compare every attempt against.
3. The prefix is fixed — so reason about what the filesystem does *after* the
   join. If the path starts at `photos/` but the filename walks back up, where
   does it land? Craft `name` to climb out of the prefix.
4. Confirm the escape by reading the challenge target outside `photos/`. Keep
   the path **as-is** so `../` is not normalised away before it is sent
   (`curl --path-as-is`, or edit the raw request in your proxy).

## 🕵️‍♂️ Going further

A forced prefix often hides a second surprise: an *absolute* `name` may discard
the prefix entirely (`os.path.join("photos", "/etc/passwd")` is just
`/etc/passwd`). Keep climbing with extra `../` to reach files elsewhere on the
container filesystem — the labs run as a non-root user inside Docker, so the
bug is real but the blast radius is contained on purpose.

## 🤔 Why it matters

"We always prepend a safe folder" is one of the most common false comforts in
real code reviews. Recognising that containment must be *checked on the resolved
path* — not assumed from a prefix — is the core takeaway, and the foundation for
the smarter (but still broken) defences in the levels ahead.

---

When you have captured the flag (or want to check the fix and the *why* behind
it), continue to **[SOLVE → SOLUTION.md](SOLUTION.md)**.
