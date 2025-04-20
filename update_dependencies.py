import subprocess

from tomlkit import item
from tomlkit.toml_file import TOMLFile

# Step 1: Get the frozen dependencies
result = subprocess.run(["uv", "pip", "freeze"], capture_output=True, text=True, check=False)
if result.returncode != 0:
    raise RuntimeError(f"`uv pip freeze` failed: {result.stderr}")
frozen_deps = [line.strip() for line in result.stdout.splitlines() if line.strip()]

# Step 2: Load pyproject.toml
pyproject_path = "pyproject.toml"
toml_file = TOMLFile(pyproject_path)
doc = toml_file.read()

# Step 3: Replace the `dependencies` field with a multi-line array
multiline_deps = item(frozen_deps)
multiline_deps.multiline(multiline=True)
doc["project"]["dependencies"] = multiline_deps

# Step 4: Save with preserved format
toml_file.write(doc)