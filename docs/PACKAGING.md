# Packaging a Game as a Standalone Executable

This engine has no runtime dependencies of its own, but a *player* still needs a
Python interpreter to run your `.py` file directly. Packaging bundles your game,
the engine, tkinter, and (optionally) a Python interpreter into a single
executable a player can run with no Python installation at all.

Everything below was verified by actually building and running the resulting
executables — including the real audio extra and real image assets — not just
copied from a tutorial. The three gotchas in [Common Problems](#common-problems)
were all genuine failures caught this way, with the working fix for each.

## Table of Contents

1. [Choosing a Tool](#1-choosing-a-tool)
2. [Basic Packaging](#2-basic-packaging)
3. [Bundling Image Assets](#3-bundling-image-assets)
4. [Bundling Real Audio (the `audio` extra)](#4-bundling-real-audio-the-audio-extra)
5. [One-File vs. One-Folder](#5-one-file-vs-one-folder)
6. [Platform Notes](#6-platform-notes)
7. [Testing Your Build](#7-testing-your-build)
8. [Common Problems](#8-common-problems)

## 1. Choosing a Tool

**[PyInstaller](https://pyinstaller.org/)** is the recommended choice — actively
maintained, explicitly supports tkinter, and works on Windows, macOS, and Linux.
Install it in your project's virtual environment, not system-wide:

```bash
pip install pyinstaller
```

(Nuitka is a reasonable alternative if you specifically want compiled, faster
startup — it's not covered here.)

## 2. Basic Packaging

For a game with no image assets and no real-audio extra installed — for
example, `asteroids_game.py`, which draws every shape procedurally and uses
only the built-in bullet/explosion/engine sounds — packaging is one command,
run from the repository root so `engine` resolves as a sibling package:

```bash
pyinstaller --onefile --paths . -n my_game examples/games/asteroids_game.py
```

- `--onefile` produces a single executable (see [section 5](#5-one-file-vs-one-folder) for the trade-off).
- `--paths .` tells PyInstaller where to find the `engine` package, exactly like running `python -m examples.games.asteroids_game` from the repo root does.
- `-n my_game` names the output; otherwise it's named after the script.

The result lands in `dist/my_game` (`dist/my_game.exe` on Windows). Copy that
one file to another machine with no Python installed and it runs.

## 3. Bundling Image Assets

If your game loads real images through `AssetManager` — like
`examples/demos/atlas.py` does — two things change.

**First**, tell PyInstaller to copy the asset folder into the bundle with
`--add-data SOURCE:DEST` (use `;` instead of `:` on Windows):

```bash
pyinstaller --onefile --paths . \
  --add-data "examples/assets:assets" \
  -n my_game my_game.py
```

This places your `examples/assets/` folder at the *root* of the bundle, as `assets/`.

**Second** — and this is the part that actually breaks silently if skipped —
don't resolve your `asset_root` from `__file__` alone. Inside a one-file build,
the entry script's `__file__` sits directly at the bundle's root, no matter how
deeply nested the original source file was. A pattern like
`Path(__file__).resolve().parents[1]`, which correctly climbs from
`examples/demos/atlas.py` up to `examples/` in normal development, instead
climbs from the bundle root up to its *parent temp directory* when frozen —
confirmed by testing: it silently resolved to `/tmp` instead of the bundle,
and the load failed with `AssetNotFoundError`.

The fix is to branch on whether you're running frozen, using the `sys.frozen`
flag and `sys._MEIPASS` path that PyInstaller sets at runtime:

```python
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    asset_root = Path(sys._MEIPASS)  # PyInstaller's extraction directory
else:
    asset_root = Path(__file__).resolve().parent

game = MyGame("My Game", (800, 600), asset_root=asset_root)
```

With both pieces in place — matching where `--add-data` put the folder to
where this code looks for it — image loading works identically to running
the game unpackaged.

## 4. Bundling Real Audio (the `audio` extra)

If you've installed the optional `audio` extra (see
[`AUDIO.md`](AUDIO.md)) so your game gets real sound instead of the
terminal-bell approximation, add one flag:

```bash
pyinstaller --onefile --paths . --hidden-import=_cffi_backend -n my_game my_game.py
```

Without `--hidden-import=_cffi_backend`, the packaged executable fails at
startup with `ModuleNotFoundError: No module named '_cffi_backend'` —
confirmed by testing. `miniaudio` is built on `cffi`, and PyInstaller's static
analysis only sees plain `import` statements in Python source; it can't see
that `cffi`'s compiled backend gets loaded from inside `miniaudio`'s own C
extension, so it never includes it unless told to.

If you don't have the `audio` extra installed at all, skip this flag — your
build doesn't need it, and `SoundGenerator` falls back to the terminal bell
exactly as it does unpackaged.

## 5. One-File vs. One-Folder

`--onefile` is the simplest to distribute (one file), but it extracts itself
to a temp directory on every launch — during testing this measurably showed
up as extra "slow frame" warnings from the engine's own debug overlay in the
first second or two after launch. If your game's frame pacing needs to be
consistent from the very first frame, drop `--onefile` in favor of the
default one-folder build:

```bash
pyinstaller --paths . -n my_game my_game.py
```

This produces `dist/my_game/` — a folder containing the executable alongside
its dependencies, with no extraction step at startup. Distribute the whole
folder (zip it) instead of a single file.

## 6. Platform Notes

Everything above was built and run on Linux for this guide. These are
standard, well-documented PyInstaller behaviors on the other platforms, not
independently verified here:

- **Windows**: add `--windowed` (alias `--noconsole`) so no console window
  flashes behind your game, and `--icon=path/to/icon.ico` for a custom
  taskbar/file icon.
- **macOS**: add `--windowed` to produce a proper `.app` bundle instead of a
  bare Unix executable.
- Build on the platform you're targeting — PyInstaller does not cross-compile;
  a Windows `.exe` must be built on Windows, and so on for each platform.

## 7. Testing Your Build

Run the packaged executable on a machine (or at minimum, a fresh virtual
environment with nothing installed) that doesn't already have Python or this
engine set up. It's easy for a build to accidentally work only because your
development environment happens to have something on `PYTHONPATH` or
`LD_LIBRARY_PATH` that the bundle doesn't actually include.

## 8. Common Problems

- **`ModuleNotFoundError: No module named '_cffi_backend'`** — you installed
  the `audio` extra but didn't add `--hidden-import=_cffi_backend`. See
  [section 4](#4-bundling-real-audio-the-audio-extra).
- **`AssetNotFoundError` for a file you know you bundled** — your asset-root
  resolution is using bare `__file__` instead of checking `sys.frozen` /
  `sys._MEIPASS`. See [section 3](#3-bundling-image-assets).
- **`ImportError: libtcl9.0.so: cannot open shared object file`** (or a
  similar `libtcl`/`libtk` error), specifically on Linux with Python
  installed via a version manager like `pyenv`, `mise`, or `asdf` rather than
  your distribution's package manager: PyInstaller's dependency scanner
  couldn't resolve the Tcl/Tk shared libraries at build time. Point it at
  your Python installation's own `lib` directory when building:

  ```bash
  LD_LIBRARY_PATH="$(python3 -c 'import sys; print(sys.prefix)')/lib" \
    pyinstaller --onefile --paths . -n my_game my_game.py
  ```

  A standard system-installed Python (via `apt`, `dnf`, Homebrew, or the
  official python.org installer) is unlikely to hit this at all.
