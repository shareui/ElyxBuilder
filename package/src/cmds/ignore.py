import os
import sys
import yaml


def loadYaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def saveYaml(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


def toUnixPath(raw: str) -> str:
    # normalize backslashes to forward slashes
    return raw.replace("\\", "/")


def resolveConfigPath() -> tuple[str, str]:
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

    return refmapPath, configPath


# maps dest name (from argparse) to config.yml key
ARRAY_KEY = {
    "all": "ignoreAll",
    "no_assets": "optionalAssets",
    "compile": "compilationIgnore",
}


def runAddIgnore(rawPath: str, target: str) -> None:
    unixPath = toUnixPath(rawPath)
    _, configPath = resolveConfigPath()

    arrayKey = ARRAY_KEY[target]
    config = loadYaml(configPath)
    arr = config.get(arrayKey)
    if not isinstance(arr, list):
        arr = []

    if unixPath in arr:
        print(f"already in {arrayKey}: {unixPath}")
        return

    arr.append(unixPath)
    config[arrayKey] = arr
    saveYaml(configPath, config)
    print(f"added to {arrayKey}: {unixPath}")


def runDelIgnore(rawIndex: str, target: str) -> None:
    try:
        index = int(rawIndex)
    except ValueError:
        print(f"error: index must be an integer, got: {rawIndex!r}", file=sys.stderr)
        sys.exit(1)

    _, configPath = resolveConfigPath()

    arrayKey = ARRAY_KEY[target]
    config = loadYaml(configPath)
    arr = config.get(arrayKey)

    if not isinstance(arr, list) or len(arr) == 0:
        print(f"error: {arrayKey} is empty", file=sys.stderr)
        sys.exit(1)

    if index < 0 or index >= len(arr):
        print(f"error: index {index} out of range (0..{len(arr) - 1})", file=sys.stderr)
        sys.exit(1)

    removed = arr.pop(index)
    config[arrayKey] = arr
    saveYaml(configPath, config)
    print(f"removed from {arrayKey}[{index}]: {removed}")
