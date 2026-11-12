# Snaptrail — Learning Guide

> A guided, **non-spoiler** path to solving this lab. It teaches the *method*,
> not the answer — the exact winning payload and the flag stay in
> [SOLUTION.md](SOLUTION.md).

## Before you start

Read the shared **[Path Traversal field guide](https://github.com/iv0ks/appsec-labs/blob/main/docs/path-traversal.md)**
first. It covers what path traversal (CWE-22) is, why it appears, and the manual
testing workflow with **Burp Suite** and **OWASP ZAP**. This guide assumes it.

## What this level teaches

**Level 2 — a forced base-path prefix.** Snaptrail always prepends the gallery
directory to whatever filename you request. The developer believes that
"always starting from `photos/`" keeps every request inside the gallery. This
is the first *apparent* defence — and the lesson is that prepending a base
directory does nothing on its own, because the join still honours `..`
components (and would even honour an absolute path).

- **Entry point:** `GET /media?name=<name>`
- **The broken defence:** a forced `photos/` prefix, with no boundary check on
  the resolved path.
- **Served directory:** `photos/` · **target:** a file one level above it.

## How to approach it

1. Open a photo through your proxy and capture the request carrying `name`.
2. Baseline the legitimate value in Repeater / Request Editor.
3. The prefix is fixed — so reason about what the filesystem does *after* the
   join. If the path starts at `photos/` but the filename walks back up, where
   does it land? Craft `name` to climb out of the prefix.
4. Keep the path **as-is** (`curl --path-as-is`, or edit the raw request) and
   confirm you can read the target outside `photos/`.

## Going further

A forced prefix often hides a second surprise: an *absolute* path in the
parameter may discard the prefix entirely. Think about what your tooling does to
`../` and how a scanner's path-traversal wordlist would enumerate this.

## Why it matters

"We always prepend a safe folder" is one of the most common false comforts in
real code reviews. Recognising that containment must be checked on the
**resolved** path — not assumed from a prefix — is the core takeaway.

When you have captured the flag (or want to check the fix), read
[SOLUTION.md](SOLUTION.md).
