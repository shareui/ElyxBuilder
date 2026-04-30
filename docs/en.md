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

### `elyb --version`

Prints the ElyxBuilder version.

---

### `elyb new <pluginname> <author>`

Scaffolds a new plugin in the current directory.

```bash
elyb new "My Plugin" myname
elyb new "My Plugin" myname -zf eaf
```

| Argument / flag | Description |
|---|---|
| `pluginname` | Plugin name |
| `author` | Author identifier |
| `-zf`, `--zipformat` | Archive extension (default: `eaf`) |

The name is normalized for file/folder names: spaces are removed with the next word capitalized (CamelCase), special characters except `_`, `-`, letters, and digits are stripped. In `meta.yml` the name is stored as-is.

Plugin ID is built as `author_PluginName`, truncated to 32 characters.

After creation, fill in the `author` field in `meta.yml` manually.

---

### `elyb build`

Packages the plugin into an archive. Must be run from the directory containing `refmap.yml`.

```bash
elyb build
elyb build -v
elyb build --no-assets
elyb build --ast
elyb build --compile
elyb build --compile --reset
elyb build -p aes-256 mypassword
```

| Flag | Description |
|---|---|
| `--no-assets` | Exclude files listed in `optionalAssets` |
| `-v`, `--verbose` | Print a detailed build log |
| `-a`, `--ast` | Check `.py` syntax via AST before building |
| `-c`, `--compile` | Compile `.py` → `.pyc` (Python 3.11) |
| `-r`, `--reset` | Clear the compilation cache before building (requires `--compile`) |
| `-p METHOD PASS` | Encrypt the archive |

`--ast` and `--compile` are mutually exclusive.

Output is written to `builds/`.

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
