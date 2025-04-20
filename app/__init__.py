"""UpToTrial - FastAPI-based Clinical Trials Search API."""

import pathlib

import tomlkit


def _get_version() -> str:
    """Get project version from pyproject.toml."""
    pyproject_path = pathlib.Path(__file__).parents[1] / "pyproject.toml"

    with pathlib.Path(pyproject_path).open("rb") as f:
        pyproject = tomlkit.parse(f.read().decode("utf-8"))

    return str(pyproject.get("project", {}).get("version", "0.0.0"))

__version__ = _get_version()
