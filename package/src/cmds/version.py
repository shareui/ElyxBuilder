import importlib.metadata

def runVersion():
    try:
        version = importlib.metadata.version("ElyxBuilder")
    except importlib.metadata.PackageNotFoundError:
        print("An error occurred due to multiple interpreters. Please reinstall the package and everything will be fine.")
        return
    print(f"ElyxBuilder v{version}")
