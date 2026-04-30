import json
import os
import re


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


def runNew(pluginname: str, author: str, zipFormat: str = "eaf"):
    normalized = normalizeName(pluginname)
    base = normalized
    cfg = loadConfig()

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

    normalizedAuthor = normalizeName(author)
    pluginId = f"{normalizedAuthor}_{normalized}"
    if len(pluginId) > 32:
        pluginId = pluginId[:32]
    # name field uses raw pluginname (not normalized)
    writeFile(
        f"{base}/meta.yml",
        f'name: {pluginname}\n'
        f'description: "{{description}}"\n'
        f'id: {pluginId}\n'
        f'version: "0.1.0"\n'
        f'author: "Enter your name"\n'
        f'app_version: "{cfg["appVersion"]}"\n'
        f'sdk_version: "{cfg["sdkVersion"]}"\n'
        f'elyx_version: "{cfg["elyxVersion"]}"\n'
        f'# icon: \n'
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
