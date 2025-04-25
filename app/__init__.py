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


try:
    # Try to load logging configuration from file.
    # This configures logging not just for the app but also for all other modules.
    import logging.config
    logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
except Exception as e:
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.warning(f"Failed to load logging configuration. Error: {e}. "
                    "Using default logging settings with DEBUG level.")

from app.main import create_app  # noqa: E402

__all__ = ["__version__", "create_app"]
