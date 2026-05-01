import json
import os
import re

CYAN = "\033[96m"
RESET = "\033[0m"


def normalizeName(raw: str) -> str:
    # remove chars except space, _, -, A-Z, a-z, 0-9
    cleaned = re.sub(r"[^ _\-a-zA-Z0-9]", "", raw)
    # split on spaces, capitalize each word after the first
    parts = cleaned.split(" ")
    result = parts[0]
    for part in parts[1:]:
        if part:
            result += part[0].upper() + part[1:]
    return result


def writeFile(path: str, content: str):
    dirName = os.path.dirname(path)
    if dirName:
        os.makedirs(dirName, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def loadConfig() -> dict:
    configPath = os.path.join(os.path.dirname(__file__), "..", "config.json")
    with open(configPath, "r", encoding="utf-8") as f:
        return json.load(f)


def promptField(label: str, default: str) -> str:
    # show label with default in cyan, return user input or default if empty
    raw = input(f"{label}[{CYAN}{default}{RESET}] ~> ")
    return raw.strip() if raw.strip() else default


def runInteractive():
    cfg = loadConfig()
    print("Enter an empty string to apply the value in [].\n")

    pluginname = promptField("name ", "MyPlugin")
    normalized = normalizeName(pluginname)

    defaultAuthor = "NoName"
    author = promptField("author ", defaultAuthor)
    normalizedAuthor = normalizeName(author)

    pluginId = f"{normalizedAuthor}_{normalized}"
    if len(pluginId) > 32:
        pluginId = pluginId[:32]
    pluginId = promptField("id ", pluginId)

    version = promptField("version ", "0.1.0")
    appVersion = promptField("app_version ", cfg["appVersion"])
    sdkVersion = promptField("sdk_version ", cfg["sdkVersion"])
    elyxVersion = promptField("elyx_version ", cfg["elyxVersion"])
    zipFormat = promptField("zipFormat ", "eaf")
    iconRaw = promptField("icon (leave empty to skip) ", "")

    writePlugin(pluginname, normalized, author, pluginId, version, appVersion, sdkVersion, elyxVersion, zipFormat, iconRaw)


def runNew(pluginname: str, author: str, zipFormat: str = "eaf"):
    normalized = normalizeName(pluginname)
    normalizedAuthor = normalizeName(author)
    cfg = loadConfig()

    pluginId = f"{normalizedAuthor}_{normalized}"
    if len(pluginId) > 32:
        pluginId = pluginId[:32]

    writePlugin(
        pluginname, normalized, author, pluginId,
        "0.1.0", cfg["appVersion"], cfg["sdkVersion"], cfg["elyxVersion"],
        zipFormat, ""
    )


def writePlugin(
    pluginname: str,
    normalized: str,
    author: str,
    pluginId: str,
    version: str,
    appVersion: str,
    sdkVersion: str,
    elyxVersion: str,
    zipFormat: str,
    icon: str
):
    base = normalized

    writeFile(
        f"{base}/.elyxbuilder/config.yml",
        f'zipFormat: {zipFormat}\n'
        f'source: {normalized}/src\n'
        f'buildNameUncompiled: "{{name}}-{{version}}"\n'
        f'buildNameCompiled: "{{name}}-{{version}}-3.11"\n'
        f'ignoreAll:\n'
        f'  - {normalized}/.elyxbuilder/cache/*\n'
        f'compilationIgnore:\n'
        f'  - {normalized}/src/main.py\n'
    )

    writeFile(
        f"{base}/locales/strings_en.json",
        '{\n  "description": "Enter plugin description"\n}\n'
    )

    writeFile(
        f"{base}/locales/strings_ru.json",
        '{\n  "description": "Введите описание плагина"\n}\n'
    )

    iconLine = f'icon: {icon}\n' if icon else '# icon: \n'
    # name field uses raw pluginname (not normalized)
    writeFile(
        f"{base}/meta.yml",
        f'name: {pluginname}\n'
        f'description: "{{description}}"\n'
        f'id: {pluginId}\n'
        f'version: "{version}"\n'
        f'author: "{author}"\n'
        f'app_version: "{appVersion}"\n'
        f'sdk_version: "{sdkVersion}"\n'
        f'elyx_version: "{elyxVersion}"\n'
        f'{iconLine}'
    )

    os.makedirs(f"{base}/res", exist_ok=True)
    open(f"{base}/res/.gitkeep", "w").close()

    writeFile(
        f"{base}/src/main.py",
        f'from base_plugin import BasePlugin\n'
        f'from android_utils import log\n'
        f'\n'
        f'class {normalized}Main(BasePlugin):\n'
        f'    def on_plugin_load(self):\n'
        f'        log("Hello, Elyx!")\n'
        f'\n'
        f'    def on_plugin_unload(self):\n'
        f'        log("Bye, Elyx!")\n'
    )

    writeFile(
        "refmap.yml",
        f'metainfo: {normalized}/meta.yml\n'
        f'main: {normalized}/src/main.py\n'
        f'assets: {normalized}/res\n'
        f'strings: {normalized}/locales\n'
        f'elyxbuilder: {normalized}/.elyxbuilder\n'
    )

    print(f"Created plugin: {normalized}")
