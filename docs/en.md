# ElyxBuilder

CLI tool for building Elyx plugins.

## Installation

Please use the releases page on GitHub: [shareui/ElyxBuilder/releases](https://github.com/shareui/ElyxBuilder/releases)

## Requirements

- Python >= 3.10
- Python 3.11 — required only for `.pyc` compilation
- pyzipper — required only for archive encryption

---

## Commands

> All commands must be run from the project root — the directory containing `refmap.yml`.

### `elyb --version`

Prints the ElyxBuilder version.

---

### `elyb new`

Scaffolds a new plugin in the current directory.

By default, opens an interactive prompt for each `meta.yml` field. Each field shows a generated default in brackets — press Enter to accept it.

```bash
elyb new
```

With `-g` / `--gen`, skips the prompt and generates the plugin immediately using the provided flags:

```bash
elyb new -g -n "My Plugin" -a myname
elyb new -g -n "My Plugin" -a myname -zf eaf
```

| Flag | Description |
|---|---|
| `-g`, `--gen` | Fast generation (non-interactive) |
| `-n`, `--name` | Plugin name (required with `--gen`) |
| `-a`, `--author` | Author identifier (required with `--gen`) |
| `-zf`, `--zipformat` | Archive extension (default: `eaf`, only with `--gen`) |

The name is normalized for file/folder names: spaces are removed with the next word capitalized (CamelCase), special characters except `_`, `-`, letters, and digits are stripped. In `meta.yml` the name is stored as-is.

Plugin ID is built as `author_PluginName`, truncated to 32 characters.

`description` is always auto-generated as a `{description}` placeholder and is not prompted.

---

### `elyb build`

Packages the plugin into an archive. Must be run from the directory containing `refmap.yml`.

```bash
elyb build
elyb build -v
elyb build --no-assets
elyb build --no-folder
elyb build --ast
elyb build --compile
elyb build --compile --reset
elyb build -p aes-256 mypassword
```

| Flag | Description |
|---|---|
| `--no-assets` | Exclude files listed in `optionalAssets` |
| `-nf`, `--no-folder` | Exclude the `elyxbuilder` directory from the archive |
| `-v`, `--verbose` | Print a detailed build log |
| `-a`, `--ast` | Check `.py` syntax via AST before building |
| `-c`, `--compile` | Compile `.py` → `.pyc` (Python 3.11) |
| `-r`, `--reset` | Clear the compilation cache before building (requires `--compile`) |
| `-p METHOD PASS` | Encrypt the archive |
| `-ni`, `--no-info` | Skip appending the elyxbuilder info block to `meta.yml` |

`--ast` and `--compile` are mutually exclusive.

Output is written to `builds/`.

#### Build info

Before packaging, elyxbuilder appends a comment block to `meta.yml` inside the archive. The source file on disk is not modified.

```yaml
# elyxbuilder info
compiled: true/false
buildNum: 5
buildDate: 2026-05-09
pythonVer: 3.11
sourceHash: a3f2...
elybVer: 0.3.0
```

Use `-ni` / `--no-info` to skip this block entirely.

#### Compilation (`--compile`)

Files in `compilationIgnore` are not compiled and are included in the archive as `.py`. All other `.py` files are replaced with compiled `.pyc`. An incremental cache is used — subsequent builds only recompile changed files.

#### Encryption (`-p`)

Requires: `pip install pyzipper`

| Method | Description |
|---|---|
| `zipcrypto` | Standard ZIP encryption |
| `aes-128` | AES 128-bit |
| `aes-192` | AES 192-bit |
| `aes-256` | AES 256-bit (recommended) |

```bash
elyb build -p aes-256 mypassword
```

---

### `elyb cached`

Shows which files have changed since the last compilation. Must be run from the directory containing `refmap.yml`.

```bash
elyb cached
```

Requires a prior build with `--compile`.

| Status | Description |
|---|---|
| `ok` | File unchanged, cache is up to date |
| `modified` | File has changed since last compilation |
| `new` | File has never been compiled |
| `ignored` | File is in `compilationIgnore` |

---

### `elyb add-ignore <path> <target>`

Adds a path to one of the ignore lists in `.elyxbuilder/config.yml`.

```bash
elyb add-ignore "MyPlugin/res/heavy.png" --no-assets
elyb add-ignore "MyPlugin/.elyxbuilder/cache/*" --all
elyb add-ignore "MyPlugin/src/helpers.py" --compile
```

| Flag | List | Effect |
|---|---|---|
| `-a`, `--all` | `ignoreAll` | Exclude from every build |
| `-na`, `--no-assets` | `optionalAssets` | Exclude when `--no-assets` is passed |
| `-c`, `--compile` | `compilationIgnore` | Skip compilation for this file |

Backslashes are normalized to forward slashes. Duplicates are not added.

---

### `elyb del-ignore <index> <target>`

Removes an entry from an ignore list by its zero-based index.

```bash
elyb del-ignore 0 --all
elyb del-ignore 2 --no-assets
elyb del-ignore 1 --compile
```

Flags are the same as `add-ignore`. The index corresponds to the position in the list in `config.yml`.

---

### `elyb stats builds`

Shows build count statistics. Must be run from the directory containing `refmap.yml`.

```bash
elyb stats builds
```

Example output:

```
Total builds: 10
Uncompiled: 6 (60%)
Compiled: 3 (30%)
Failed: 1 (10%)
```

---

### `elyb stats lines`

Counts lines of code in the plugin. Must be run from the directory containing `refmap.yml`.

```bash
elyb stats lines
```

Counts only `.py` files in the `source` directory (from `config.yml`). Example output:

```
Lines count statistics for plugin MyPlugin:
MyPlugin/src: 142 (Python only)
```

With `-a` / `--all`, counts all non-binary files in the plugin root directory and `refmap.yml`:

```bash
elyb stats lines --all
```

Example output:

```
Total lines count statistics for plugin MyPlugin:
.py: 142
.yml: 30
Total: 172
```

With `-add` / `--additional`, includes additional directories relative to `cwd` (requires `--all`):

```bash
elyb stats lines --all --additional docs scripts
```

| Flag | Description |
|---|---|
| `-a`, `--all` | Count all non-binary files in plugin root |
| `-add DIR...`, `--additional DIR...` | Add extra directories to count (requires `--all`) |

---

### `elyb stats size`

Shows file size statistics. Must be run from the directory containing `refmap.yml`.

```bash
elyb stats size
```

Shows the total size of `.py` files in the `source` directory (from `config.yml`). Example output:

```
The size of the directory MyPlugin/src: 4.21 KB (0.0 MB)
Python only
```

With `-a` / `--all`, counts all non-binary files in the plugin root directory and `refmap.yml`:

```bash
elyb stats size --all
```

Example output:

```
File size statistics for plugin MyPlugin:
.py: 4.21 KB (0.0 MB)
.yml: 0.83 KB (0.0 MB)
```

With `-add` / `--additional`, includes additional directories relative to `cwd` (requires `--all`):

```bash
elyb stats size --all --additional docs scripts
```

| Flag | Description |
|---|---|
| `-a`, `--all` | Count all non-binary files in plugin root |
| `-add DIR...`, `--additional DIR...` | Add extra directories to count (requires `--all`) |

---

### `elyb stats files`

Shows file count by extension. Must be run from the directory containing `refmap.yml`.

```bash
elyb stats files
```

Counts all files in the plugin root directory by extension. Example output:

```
File count statistics for plugin MyPlugin:
.py: 5
.yml: 3
Total: 8
```

With `-a` / `--all`, also includes `refmap.yml`:

```bash
elyb stats files --all
```

With `-add` / `--additional`, includes additional directories relative to `cwd`:

```bash
elyb stats files --all --additional docs scripts
```

| Flag | Description |
|---|---|
| `-a`, `--all` | Include `refmap.yml` and additional directories |
| `-add DIR...`, `--additional DIR...` | Add extra directories to count (requires `--all`) |
