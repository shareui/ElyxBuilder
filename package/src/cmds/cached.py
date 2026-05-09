import json
import os
import sys
import time
import yaml


GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


def loadYaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def loadManifest(manifestPath: str) -> dict:
    if not os.path.exists(manifestPath):
        return {}
    with open(manifestPath, "r", encoding="utf-8") as f:
        return json.load(f)


def formatSize(byteCount: int) -> str:
    if byteCount < 1024:
        return f"{byteCount} B"
    if byteCount < 1024 * 1024:
        return f"{byteCount / 1024:.1f} KB"
    return f"{byteCount / (1024 * 1024):.1f} MB"


def formatAge(mtime: float) -> str:
    # how long ago the .pyc was written
    delta = int(time.time() - mtime)
    if delta < 60:
        return f"{delta}s ago"
    if delta < 3600:
        return f"{delta // 60}m ago"
    if delta < 86400:
        return f"{delta // 3600}h ago"
    return f"{delta // 86400}d ago"


def runCached() -> None:
    cwd = os.getcwd()
    refmapPath = os.path.join(cwd, "refmap.yml")

    if not os.path.exists(refmapPath):
        print("error: refmap.yml not found in current directory", file=sys.stderr)
        sys.exit(1)

    refmap = loadYaml(refmapPath)
    builderRelPath = refmap.get("elyxbuilder")
    if not builderRelPath:
        print("error: refmap.yml missing key: elyxbuilder", file=sys.stderr)
        sys.exit(1)

    builderDir = os.path.join(cwd, builderRelPath)
    configPath = os.path.join(builderDir, "config.yml")
    if not os.path.exists(configPath):
        print(f"error: config.yml not found: {configPath}", file=sys.stderr)
        sys.exit(1)

    config = loadYaml(configPath)
    sourceRelPath = config.get("source")
    if not sourceRelPath:
        print("error: config.yml missing key: source", file=sys.stderr)
        sys.exit(1)

    sourceDir = os.path.join(cwd, sourceRelPath)
    cacheDir = os.path.join(cwd, ".elyx", "cache", "python311")
    manifestPath = os.path.join(cacheDir, "manifest.json")

    if not os.path.exists(manifestPath):
        print("No cache found. Run elyb build -c first.")
        return

    manifest = loadManifest(manifestPath)

    rawIgnore = config.get("compilationIgnore") or []
    ignoreAbsPaths = {os.path.normpath(os.path.join(cwd, p)) for p in rawIgnore}

    cacheDirDisplay = os.path.join(".elyx", "cache", "python311").replace(os.sep, "/")
    print(f"Cache: {cacheDirDisplay}")

    counts = {"modified": 0, "new": 0, "ok": 0, "ignored": 0}
    rows: list[tuple[str, str, str]] = []

    for root, dirs, files in os.walk(sourceDir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for file in files:
            if not file.endswith(".py"):
                continue
            absPath = os.path.join(root, file)
            relPath = os.path.relpath(absPath, sourceDir).replace(os.sep, "/")

            if os.path.normpath(absPath) in ignoreAbsPaths:
                rows.append(("ignored", relPath, ""))
                counts["ignored"] += 1
                continue

            stat = os.stat(absPath)
            entry = manifest.get(relPath)

            if entry is None:
                info = formatSize(stat.st_size)
                rows.append(("new", relPath, info))
                counts["new"] += 1
                continue

            if entry.get("mtime") != stat.st_mtime or entry.get("size") != stat.st_size:
                pycRelPath = relPath[:-3] + ".pyc"
                pycAbsPath = os.path.join(cacheDir, pycRelPath.replace("/", os.sep))
                age = formatAge(os.stat(pycAbsPath).st_mtime) if os.path.exists(pycAbsPath) else "no pyc"
                info = f"{formatSize(stat.st_size)}, cached {age}"
                rows.append(("modified", relPath, info))
                counts["modified"] += 1
                continue

            rows.append(("ok", relPath, ""))
            counts["ok"] += 1

    # column width for alignment
    maxPathLen = max((len(r[1]) for r in rows), default=0)

    for status, relPath, info in rows:
        paddedPath = relPath.ljust(maxPathLen)
        if status == "modified":
            label = f"{YELLOW}  modified{RESET}"
            detail = f"  {DIM}({info}){RESET}" if info else ""
            print(f"{label}  {paddedPath}{detail}")
        elif status == "new":
            label = f"{RED}  new      {RESET}"
            detail = f"  {DIM}({info}){RESET}" if info else ""
            print(f"{label}  {paddedPath}{detail}")
        elif status == "ignored":
            print(f"{DIM}  ignored   {relPath}{RESET}")
        else:
            print(f"{GREEN}  ok       {RESET}  {DIM}{paddedPath}{RESET}")

    parts = []
    if counts["modified"]:
        parts.append(f"{counts['modified']} modified")
    if counts["new"]:
        parts.append(f"{counts['new']} new")
    if counts["ok"]:
        parts.append(f"{counts['ok']} ok")
    if counts["ignored"]:
        parts.append(f"{counts['ignored']} ignored")

    print(f"\n{', '.join(parts)}")
