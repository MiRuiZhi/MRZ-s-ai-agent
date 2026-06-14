from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


SERVICE_ROOT = Path(__file__).resolve().parents[2]


def load_reactor_tool_dotenv(
    dotenv_path: str | os.PathLike[str] | None = None,
    *,
    service_root: str | os.PathLike[str] | None = None,
) -> bool:
    """Load only reactor-tool's own .env file.

    python-dotenv's default search walks parent directories. In this monorepo
    that can accidentally load the root Compose .env into local tool-runtime
    processes, mixing Docker paths into host runs.
    """

    if dotenv_path is None:
        root = Path(service_root) if service_root is not None else SERVICE_ROOT
        dotenv_file = root / ".env"
    else:
        dotenv_file = Path(dotenv_path)

    if not dotenv_file.is_file():
        return False
    return load_dotenv(dotenv_path=dotenv_file, override=False)
