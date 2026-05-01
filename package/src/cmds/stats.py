import os
import yaml

GREEN = "\033[32m"
RESET = "\033[0m"

BINARY_EXTENSIONS = {
    ".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".mp3", ".mp4", ".wav", ".ogg", ".flac",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".eaf",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".db", ".sqlite",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".ttf", ".otf", ".woff", ".woff2",
}

def countLines(path: str) -> int:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f)

def isBinary(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in BINARY_EXTENSIONS

def countLinesInDir(dirPath: str, extFilter: str | None = None, excludeDir: str | None = None) -> dict[str, int]:
    # returns {ext: lineCount}, extFilter=".py" limits to that ext only
    # excludeDir: absolute path of a directory to skip entirely
    result: dict[str, int] = {}
    for root, dirs, files in os.walk(dirPath):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        if excludeDir is not None:
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != os.path.abspath(excludeDir)]
        for file in files:
            absPath = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower() or "(no ext)"
            if extFilter is not None:
                if ext != extFilter:
                    continue
            elif isBinary(absPath):
                continue
            result[ext] = result.get(ext, 0) + countLines(absPath)
    return result

def runStatLines(
    pluginDir: str,
    sourceRelPath: str,
    pluginName: str,
    cwd: str,
    refmapPath: str,
    allMode: bool,
    additionalDirs: list[str],
    builderDir: str,
) -> None:
    if not allMode:
        sourceDir = os.path.join(cwd, sourceRelPath)
        counts = countLinesInDir(sourceDir, extFilter=".py", excludeDir=builderDir)
        total = sum(counts.values())
        print(f"Lines count statistics for plugin {pluginName}:")
        print(f"{sourceRelPath}: {GREEN}{total}{RESET} (Python only)")
        return

    # collect from pluginDir + refmap.yml + additionalDirs
    counts: dict[str, int] = countLinesInDir(pluginDir, excludeDir=builderDir)

    # refmap.yml itself
    refmapExt = os.path.splitext(refmapPath)[1].lower() or "(no ext)"
    if not isBinary(refmapPath):
        counts[refmapExt] = counts.get(refmapExt, 0) + countLines(refmapPath)

    for relDir in additionalDirs:
        absDir = os.path.join(cwd, relDir)
        if not os.path.isdir(absDir):
            print(f"warning: additional directory not found: {relDir}")
            continue
        dirCounts = countLinesInDir(absDir, excludeDir=builderDir)
        for ext, n in dirCounts.items():
            counts[ext] = counts.get(ext, 0) + n

    total = sum(counts.values())
    print(f"Total lines count statistics for plugin {pluginName}:")
    for ext, n in sorted(counts.items()):
        print(f"{ext}: {GREEN}{n}{RESET}")
    print(f"Total: {GREEN}{total}{RESET}")

def formatSize(bytesCount: int) -> str:
    kb = bytesCount / 1024
    mb = kb / 1024
    return f"{kb:.2f} KB ({mb:.1f} MB)"

def sizeOfDir(dirPath: str, extFilter: str | None = None, excludeDir: str | None = None) -> dict[str, int]:
    # returns {ext: bytes}, extFilter=".py" limits to that ext only
    # excludeDir: absolute path of a directory to skip entirely
    result: dict[str, int] = {}
    for root, dirs, files in os.walk(dirPath):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        if excludeDir is not None:
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != os.path.abspath(excludeDir)]
        for file in files:
            absPath = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower() or "(no ext)"
            if extFilter is not None:
                if ext != extFilter:
                    continue
            elif isBinary(absPath):
                continue
            result[ext] = result.get(ext, 0) + os.path.getsize(absPath)
    return result

def runStatSize(
    pluginDir: str,
    sourceRelPath: str,
    pluginName: str,
    cwd: str,
    refmapPath: str,
    allMode: bool,
    additionalDirs: list[str],
    builderDir: str,
) -> None:
    if not allMode:
        sourceDir = os.path.join(cwd, sourceRelPath)
        sizes = sizeOfDir(sourceDir, extFilter=".py", excludeDir=builderDir)
        total = sum(sizes.values())
        print(f"The size of the directory {sourceRelPath}: {GREEN}{formatSize(total)}{RESET}")
        print("Python only")
        return

    # collect from pluginDir + refmap.yml + additionalDirs
    sizes: dict[str, int] = sizeOfDir(pluginDir, excludeDir=builderDir)

    refmapExt = os.path.splitext(refmapPath)[1].lower() or "(no ext)"
    if not isBinary(refmapPath):
        sizes[refmapExt] = sizes.get(refmapExt, 0) + os.path.getsize(refmapPath)

    for relDir in additionalDirs:
        absDir = os.path.join(cwd, relDir)
        if not os.path.isdir(absDir):
            print(f"warning: additional directory not found: {relDir}")
            continue
        dirSizes = sizeOfDir(absDir, excludeDir=builderDir)
        for ext, n in dirSizes.items():
            sizes[ext] = sizes.get(ext, 0) + n

    print(f"File size statistics for plugin {pluginName}:")
    for ext, n in sorted(sizes.items()):
        print(f"{ext}: {GREEN}{formatSize(n)}{RESET}")
    totalSize = sum(sizes.values())
    print(f"Total: {GREEN}{formatSize(totalSize)}{RESET}")

def countFilesInDir(dirPath: str, excludeDir: str | None = None) -> dict[str, int]:
    result: dict[str, int] = {}
    for root, dirs, files in os.walk(dirPath):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        if excludeDir is not None:
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != os.path.abspath(excludeDir)]
        for file in files:
            ext = os.path.splitext(file)[1].lower() or "(no ext)"
            result[ext] = result.get(ext, 0) + 1
    return result

def runStatFiles(
    pluginDir: str,
    pluginName: str,
    cwd: str,
    refmapPath: str,
    allMode: bool,
    additionalDirs: list[str],
    builderDir: str,
) -> None:
    if not allMode:
        counts = countFilesInDir(pluginDir, excludeDir=builderDir)
        total = sum(counts.values())
        print(f"File count statistics for plugin {pluginName}:")
        for ext, n in sorted(counts.items()):
            print(f"{ext}: {GREEN}{n}{RESET}")
        print(f"Total: {GREEN}{total}{RESET}")
        return

    counts: dict[str, int] = countFilesInDir(pluginDir, excludeDir=builderDir)

    refmapExt = os.path.splitext(refmapPath)[1].lower() or "(no ext)"
    counts[refmapExt] = counts.get(refmapExt, 0) + 1

    for relDir in additionalDirs:
        absDir = os.path.join(cwd, relDir)
        if not os.path.isdir(absDir):
            print(f"warning: additional directory not found: {relDir}")
            continue
        dirCounts = countFilesInDir(absDir, excludeDir=builderDir)
        for ext, n in dirCounts.items():
            counts[ext] = counts.get(ext, 0) + n

    total = sum(counts.values())
    print(f"Total file count statistics for plugin {pluginName}:")
    for ext, n in sorted(counts.items()):
        print(f"{ext}: {GREEN}{n}{RESET}")
    print(f"Total: {GREEN}{total}{RESET}")

def loadStats(statsPath: str) -> dict:
    if not os.path.exists(statsPath):
        return {"builds": 0, "compiledBuilds": 0, "uncompiledBuilds": 0, "failedBuilds": 0}
    with open(statsPath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {
        "builds": data.get("builds", 0),
        "compiledBuilds": data.get("compiledBuilds", 0),
        "uncompiledBuilds": data.get("uncompiledBuilds", 0),
        "failedBuilds": data.get("failedBuilds", 0),
    }

def saveStats(statsPath: str, stats: dict) -> None:
    with open(statsPath, "w", encoding="utf-8") as f:
        yaml.safe_dump(stats, f, default_flow_style=False)

def incrementBuildStats(builderDir: str, compiled: bool) -> None:
    statsPath = os.path.join(builderDir, "stats.yml")
    stats = loadStats(statsPath)
    stats["builds"] += 1
    if compiled:
        stats["compiledBuilds"] += 1
    else:
        stats["uncompiledBuilds"] += 1
    saveStats(statsPath, stats)

def incrementFailedBuildStats(builderDir: str) -> None:
    statsPath = os.path.join(builderDir, "stats.yml")
    stats = loadStats(statsPath)
    stats["builds"] += 1
    stats["failedBuilds"] += 1
    saveStats(statsPath, stats)

def runStatBuilds(builderDir: str) -> None:
    statsPath = os.path.join(builderDir, "stats.yml")
    stats = loadStats(statsPath)
    total = stats["builds"]
    compiled = stats["compiledBuilds"]
    uncompiled = stats["uncompiledBuilds"]
    failed = stats["failedBuilds"]

    def pct(n: int) -> str:
        if total == 0:
            return "0%"
        return f"{round(n / total * 100)}%"

    print(f"Total builds: {total}")
    print(f"Uncompiled: {uncompiled} ({pct(uncompiled)})")
    print(f"Compiled: {compiled} ({pct(compiled)})")
    print(f"Failed: {failed} ({pct(failed)})")
