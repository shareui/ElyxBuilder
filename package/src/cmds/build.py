import ast
import fnmatch
import json
import os
import re
import subprocess
import sys
import zipfile
import yaml

def loadYaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def resolveBuildName(template: str, meta: dict) -> str:
    def replace(match):
        key = match.group(1)
        value = meta.get(key)
        if value is None:
            raise KeyError(f"meta.yml missing field: {key}")
        return str(value)
    return re.sub(r"\{(\w+)\}", replace, template)

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"

ENCRYPTION_METHODS: dict[str, tuple[str, int | None]] = {
    "zipcrypto": ("zipcrypto", None),
    "aes-128":   ("aes", 128),
    "aes-192":   ("aes", 192),
    "aes-256":   ("aes", 256),
}

def printEncryptionHelp() -> None:
    print("Available encryption methods:\n")
    print("  zipcrypto   Standard ZIP encryption, compatible with most archivers")
    print("  aes-128     AES encryption, 128-bit key")
    print("  aes-192     AES encryption, 192-bit key")
    print("  aes-256     AES encryption, 256-bit key (recommended)")
    print("\nUsage: elyb build -p <method> <password>")

def resolveEncryption(method: str, password: str) -> tuple[bool, object, int | None]:
    if method not in ENCRYPTION_METHODS:
        print(f"{RED}error: unknown encryption method: {method!r}{RESET}\n")
        printEncryptionHelp()
        return False, None, None
    try:
        import pyzipper
    except ImportError:
        print("pyzipper is required for encryption.")
        print("Install it with: pip install pyzipper")
        return False, None, None

    _, aesStrength = ENCRYPTION_METHODS[method]
    return True, pyzipper, aesStrength


def openArchive(archivePath: str, encryptMethod: str | None, password: str | None, pyzipper: object):
    if encryptMethod is None:
        return zipfile.ZipFile(archivePath, "w", zipfile.ZIP_DEFLATED)

    _, aesStrength = ENCRYPTION_METHODS[encryptMethod]
    if aesStrength is not None:
        zf = pyzipper.AESZipFile(archivePath, "w", compression=pyzipper.ZIP_DEFLATED)
        zf.setencryption(pyzipper.WZ_AES, nbits=aesStrength)
    else:
        zf = pyzipper.AESZipFile(archivePath, "w", compression=pyzipper.ZIP_DEFLATED)
        zf.setencryption(pyzipper.WZ_ZIP2)
    zf.setpassword(password.encode())
    return zf

def findPython311() -> str | None:
    candidates = ["python3.11", "python3", "python"]
    if sys.platform == "win32":
        candidates = ["python3.11", "python3", "python", "py"]
    for name in candidates:
        try:
            result = subprocess.run(
                [name, "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and "3.11" in result.stdout + result.stderr:
                return name
        except FileNotFoundError:
            continue
    return None

def loadManifest(manifestPath: str) -> dict:
    if not os.path.exists(manifestPath):
        return {}
    with open(manifestPath, "r", encoding="utf-8") as f:
        return json.load(f)

def saveManifest(manifestPath: str, manifest: dict) -> None:
    os.makedirs(os.path.dirname(manifestPath), exist_ok=True)
    with open(manifestPath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def compileSourceFiles(sourceDir: str, cacheDir: str, ignoreAbsPaths: set[str], log) -> tuple[bool, dict]:
    python311 = findPython311()
    if python311 is None:
        print(
            "Please install Python3.11 for compilation. "
            "After installation, reinstall the ElyxBuilder package."
        )
        return False, {}

    manifestPath = os.path.join(cacheDir, "manifest.json")
    manifest = loadManifest(manifestPath)
    compiled = 0
    cached = 0

    for root, dirs, files in os.walk(sourceDir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for file in files:
            if not file.endswith(".py"):
                continue
            absPath = os.path.join(root, file)
            if os.path.normpath(absPath) in ignoreAbsPaths:
                log(f"  compile: skip {os.path.relpath(absPath, sourceDir)}")
                continue

            relPath = os.path.relpath(absPath, sourceDir).replace(os.sep, "/")
            stat = os.stat(absPath)
            entry = manifest.get(relPath)

            pycRelPath = relPath[:-3] + ".pyc"
            pycAbsPath = os.path.join(cacheDir, pycRelPath.replace("/", os.sep))

            cacheHit = (
                entry is not None
                and entry.get("mtime") == stat.st_mtime
                and entry.get("size") == stat.st_size
                and os.path.exists(pycAbsPath)
            )

            if cacheHit:
                log(f"  compile: cached {relPath}")
                cached += 1
                continue

            os.makedirs(os.path.dirname(pycAbsPath), exist_ok=True)
            result = subprocess.run(
                [python311, "-c",
                 f"import py_compile; py_compile.compile({absPath!r}, cfile={pycAbsPath!r}, doraise=True)"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"{RED}Compilation failed:{RESET}")
                print(f"{RED}{result.stderr.strip()}{RESET}")
                return False, manifest

            manifest[relPath] = {"mtime": stat.st_mtime, "size": stat.st_size}
            log(f"  compile: {relPath}")
            compiled += 1

    saveManifest(manifestPath, manifest)
    log(f"compile: {compiled} compiled, {cached} from cache")
    return True, manifest


def pycCachePath(sourceDir: str, cacheDir: str, pyAbsPath: str) -> str:
    relPath = os.path.relpath(pyAbsPath, sourceDir).replace(os.sep, "/")
    pycRelPath = relPath[:-3] + ".pyc"
    return os.path.join(cacheDir, pycRelPath.replace("/", os.sep))


def checkAst(sourceDir: str, verbose: bool, log) -> bool:
    for root, dirs, files in os.walk(sourceDir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for file in files:
            if not file.endswith(".py"):
                continue
            absPath = os.path.join(root, file)
            relPath = os.path.relpath(absPath, sourceDir).replace(os.sep, "/")
            log(f"  ast check: {relPath}")
            try:
                with open(absPath, "r", encoding="utf-8") as f:
                    ast.parse(f.read(), filename=relPath)
            except SyntaxError as e:
                print(f"{RED}Failed to complete build:{RESET}")
                print(f"{RED}{e}{RESET}")
                return False
    return True


def runBuild(noAssets: bool = False, verbose: bool = False, checkAstFlag: bool = False, compileFlag: bool = False, resetCache: bool = False, encryptMethod: str | None = None, encryptPassword: str | None = None):
    def log(msg: str) -> None:
        if verbose:
            print(f"{DIM}{msg}{RESET}")

    def fail(msg: str) -> None:
        print(f"{RED}error: {msg}{RESET}")

    if resetCache and not compileFlag:
        fail("--reset requires --compile")
        return

    pyzipperModule = None
    aesStrength = None
    if encryptMethod is not None:
        ok, pyzipperModule, aesStrength = resolveEncryption(encryptMethod, encryptPassword)
        if not ok:
            return
        log(f"encryption: {encryptMethod}")

    cwd = os.getcwd()
    refmapPath = os.path.join(cwd, "refmap.yml")
    log(f"looking for refmap: {refmapPath}")

    if not os.path.exists(refmapPath):
        fail("refmap.yml not found in current directory")
        return

    refmap = loadYaml(refmapPath)
    log("refmap.yml loaded")

    builderRelPath = refmap.get("elyxbuilder")
    if not builderRelPath:
        fail("refmap.yml missing key: elyxbuilder")
        return

    builderDir = os.path.join(cwd, builderRelPath)
    log(f"builder dir: {builderDir}")

    if not os.path.isdir(builderDir):
        fail(f"builder directory not found: {builderDir}")
        return

    configPath = os.path.join(builderDir, "config.yml")
    log(f"looking for config: {configPath}")

    if not os.path.exists(configPath):
        fail(f"config.yml not found in {builderDir}")
        return

    config = loadYaml(configPath)
    log("config.yml loaded")

    excludedAssets: set[str] = set()
    if noAssets:
        rawAssets = config.get("optionalAssets")
        if isinstance(rawAssets, list):
            excludedAssets = set(rawAssets)
        log(f"--no-assets: excluding {len(excludedAssets)} asset(s): {sorted(excludedAssets) if excludedAssets else '(none listed)'}")

    rawIgnoreAll = config.get("ignoreAll")
    ignoreAll: list[str] = rawIgnoreAll if isinstance(rawIgnoreAll, list) else []
    log(f"ignoreAll: {len(ignoreAll)} pattern(s)")

    zipFormat = config.get("zipFormat")
    if not zipFormat:
        fail("config.yml missing key: zipFormat")
        return

    buildNameUncompiled = config.get("buildNameUncompiled")
    if not buildNameUncompiled:
        fail("config.yml missing key: buildNameUncompiled")
        return

    if compileFlag:
        buildNameTemplate = config.get("buildNameCompiled")
        if not buildNameTemplate:
            fail("config.yml missing key: buildNameCompiled")
            return
    else:
        buildNameTemplate = buildNameUncompiled

    log(f"zip format: {zipFormat}, build name template: {buildNameTemplate}")

    metaRelPath = refmap.get("metainfo")
    if not metaRelPath:
        fail("refmap.yml missing key: metainfo")
        return

    metaPath = os.path.join(cwd, metaRelPath)
    log(f"looking for metainfo: {metaPath}")

    if not os.path.exists(metaPath):
        fail(f"meta.yml not found: {metaPath}")
        return

    meta = loadYaml(metaPath)
    log("metainfo loaded")

    try:
        buildName = resolveBuildName(buildNameTemplate, meta)
    except KeyError as e:
        fail(str(e))
        return

    archiveName = f"{buildName}.{zipFormat}"
    log(f"resolved archive name: {archiveName}")

    buildsDir = os.path.join(cwd, "builds")
    os.makedirs(buildsDir, exist_ok=True)

    archivePath = os.path.join(buildsDir, archiveName)
    log(f"output path: {archivePath}")

    # plugin folder is parent of the builder dir (e.g. MyPlugin/.elyxbuilder -> MyPlugin)
    pluginDir = os.path.dirname(builderDir)

    # arc base is parent of pluginDir so plugin folder name is preserved in archive
    arcBase = os.path.dirname(os.path.normpath(pluginDir))

    log(f"plugin dir: {pluginDir}")
    log(f"arc base: {arcBase}")

    sourceRelPath = config.get("source")

    if checkAstFlag:
        if not sourceRelPath:
            fail("config.yml missing key: source (required for --ast)")
            return
        sourceDir = os.path.join(cwd, sourceRelPath)
        log(f"ast: scanning {sourceDir}")
        if not checkAst(sourceDir, verbose, log):
            return

    if compileFlag:
        if not sourceRelPath:
            fail("config.yml missing key: source (required for --compile)")
            return
        sourceDir = os.path.join(cwd, sourceRelPath)
        cacheDir = os.path.join(builderDir, "cache", "python311")

        if resetCache and os.path.exists(cacheDir):
            import shutil
            shutil.rmtree(cacheDir)
            log("compile: cache cleared")

        rawIgnore = config.get("compilationIgnore") or []
        ignoreAbsPaths = {os.path.normpath(os.path.join(cwd, p)) for p in rawIgnore}
        log(f"compile: scanning {sourceDir}, ignoring {len(ignoreAbsPaths)} file(s)")

        ok, _ = compileSourceFiles(sourceDir, cacheDir, ignoreAbsPaths, log)
        if not ok:
            return

    fileCount = 0
    skippedCount = 0

    with openArchive(archivePath, encryptMethod, encryptPassword, pyzipperModule) as zf:
        # refmap path relative to cwd, not just filename
        refmapArcName = os.path.relpath(refmapPath, cwd).replace(os.sep, "/")
        zf.write(refmapPath, refmapArcName)
        log(f"  + {refmapArcName}")
        fileCount += 1

        for root, dirs, files in os.walk(pluginDir):
            dirs[:] = [d for d in dirs if d != "__pycache__"]

            relDir = os.path.relpath(root, arcBase).replace(os.sep, "/")
            dirInfo = zipfile.ZipInfo(relDir + "/")
            zf.writestr(dirInfo, "")
            log(f"  d {relDir}/")

            for file in files:
                absPath = os.path.join(root, file)
                arcName = relDir + "/" + file
                if any(fnmatch.fnmatch(arcName, pattern) for pattern in ignoreAll):
                    log(f"  - {arcName} (ignoreAll)")
                    skippedCount += 1
                    continue
                if excludedAssets and arcName in excludedAssets:
                    log(f"  - {arcName} (excluded)")
                    skippedCount += 1
                    continue
                if compileFlag and file.endswith(".py"):
                    normalizedAbs = os.path.normpath(absPath)
                    if normalizedAbs in ignoreAbsPaths:
                        # ignored from compilation — include as .py as-is
                        zf.write(absPath, arcName)
                        log(f"  + {arcName} (not compiled)")
                        fileCount += 1
                        continue
                    pycPath = pycCachePath(sourceDir, cacheDir, absPath)
                    pycArcName = relDir + "/" + file[:-3] + ".pyc"
                    zf.write(pycPath, pycArcName)
                    log(f"  + {pycArcName} (compiled from {file})")
                    fileCount += 1
                    continue
                zf.write(absPath, arcName)
                log(f"  + {arcName}")
                fileCount += 1

    if verbose:
        log(f"packed {fileCount} file(s), skipped {skippedCount} file(s)")

    relArchivePath = os.path.join("builds", archiveName)
    print(f"{GREEN}Successful build at {relArchivePath}!{RESET}")
