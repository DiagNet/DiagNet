import importlib.resources


def list_python_files():
    files = []
    # networktests muss ein Python-Package sein (Ordner mit __init__.py)
    package = "networktests.testcases"
    for resource in importlib.resources.files(package).iterdir():
        if resource.suffix == ".py" and resource.is_file():
            files.append(resource.name)
    return files


if __name__ == "__main__":
    print(list_python_files())
