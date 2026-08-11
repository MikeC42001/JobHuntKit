# Installing the prerequisites

JobHuntKit needs three things: **Python 3.8+**, **Node.js**, and **a Chromium-family browser**.
Nothing else, and nothing from `pip`.

The README has the short copy-paste version. This page is for when that doesn't just work — which
on Windows, it sometimes doesn't, for reasons that are worth knowing about.

Whatever you do, the check at the end is the same:

```bash
bash scripts/preflight.sh
```

---

## Windows

### Run everything from Git Bash

Not optional. Every renderer is a Bash script, so PowerShell and `cmd` cannot run them — a `.sh`
file in PowerShell either opens in an editor or errors. Git Bash comes with
[Git for Windows](https://git-scm.com/download/win); install that and use the "Git Bash" terminal
for every command in these docs.

### With winget

`winget` ships as part of App Installer on Windows 11 and current Windows 10, so it's usually
already there:

```bash
winget --version
```

If that prints a version:

```bash
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
winget install --id OpenJS.NodeJS.LTS -e
```

If it errors instead — LTSC and Server editions, offline images, and some managed machines don't
have it, and it can be blocked by policy — use the downloads below.

### Without winget

| | |
|---|---|
| Git (includes Git Bash) | https://git-scm.com/download/win |
| Python | https://www.python.org/downloads/windows/ |
| Node.js (LTS) | https://nodejs.org |
| Browser | Edge is already installed. Nothing to do. |

**In the Python installer, tick "Add python.exe to PATH" on the first screen.** It is off by
default, it's easy to click past, and skipping it is the single most common way this ends up
half-working: Python installs fine, and then nothing can find it.

**After installing anything, close your terminal and open a new one.** A running shell keeps the
PATH it started with, so a fresh install is invisible to it.

### Why `python3` isn't the command on Windows

Two separate things, both worth knowing:

1. **The python.org installer gives you `python` and `py`, not `python3`.** On macOS and Linux
   `python3` is the normal name; on Windows it usually doesn't exist at all.
2. **There is usually a `python3` on PATH anyway, and it isn't Python.** Windows ships an "App
   Execution Alias" — a stub at `AppData\Local\Microsoft\WindowsApps\python3` that opens the
   Microsoft Store instead of running anything. It looks installed to anything that checks by
   name, then fails when actually run.

JobHuntKit's own scripts handle this: they try `python3`, `python`, and `py` in turn, and accept
one only if it actually executes and reports Python 3.8 or newer — so the Store stub is skipped
rather than picked. You only need to care when **you** type a command, like
`python3 scripts/init_workspace.py` in the docs. On Windows, use `python` there.

### Python is installed but nothing finds it

Either it wasn't added to PATH, or it's somewhere unusual. `scripts/preflight.sh` looks in the
common install locations, so start there — it will often find it and tell you where.

To use it without reinstalling, point at it directly:

```bash
export PYTHON_BIN="/c/Program Files/Python312/python.exe"   # your actual path
bash scripts/preflight.sh
```

Add that `export` line to `~/.bashrc` to make it stick across Git Bash sessions. Or reinstall
Python with the PATH checkbox ticked, which is tidier.

---

## macOS

```bash
brew install git python node
```

Chrome, Edge, Chromium or Brave — any one of them. Safari cannot be used: the renderer drives a
headless Chromium via `--print-to-pdf`, which is not something Safari offers.

---

## Linux (Debian/Ubuntu)

```bash
sudo apt update && sudo apt install -y git python3 nodejs npm chromium-browser
```

On other distributions the package names differ (`chromium`, `google-chrome-stable`), but the
three requirements are the same. If `apt`'s Node.js is too old for `marked`, use
[nodesource](https://github.com/nodesource/distributions) or `nvm`.

---

## Reading `preflight.sh`

```
JobHuntKit preflight
  ok    shell    MINGW64_NT-10.0-19045 — Git Bash or equivalent
  ok    python   Python 3.11.9 — python3
  ok    node     v24.4.0 — /usr/bin/node
  ok    browser  /c/Program Files/Google/Chrome/Application/chrome.exe

preflight: all good — run 'bash demo.sh'.
```

One line per requirement. Anything missing is printed as `MISSING`, with what to install, and the
script exits non-zero. `demo.sh` runs it first in quiet mode, so a missing requirement is a
checklist rather than a stack trace three steps into a render.

If it reports Python at a full path rather than a bare name, it found one that isn't on your PATH.
That works, but only because the scripts search for it — see above for making it permanent.

## Overrides

Both take a path and win over everything else:

| | |
|---|---|
| `PYTHON_BIN` | the Python to run `engine/*.py` with |
| `BROWSER_BIN` | the browser to render PDFs with (or `render.browser_bin` in `config.json`) |

If either is set but doesn't work, the scripts say so and stop rather than quietly falling back to
something else — an override you deliberately set should not be ignored.

---

Next: **[GETTING-STARTED.md](GETTING-STARTED.md)** builds your own content layer, step by step.
