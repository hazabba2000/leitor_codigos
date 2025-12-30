from __future__ import annotations

from pathlib import Path
import os
import sys

APP_NAME = "leitor_codigos"


def base_dir() -> Path:
    """Base no dev e no PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    """Caminho absoluto para qualquer recurso empacotado/da raiz."""
    return base_dir().joinpath(*parts)


def asset_path(*parts: str) -> Path:
    """Caminho absoluto para assets/."""
    return base_dir() / "assets" / Path(*parts)


def user_data_dir() -> Path:
    """Pasta gravável do usuário (Linux)."""
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else (Path.home() / ".local" / "share")
    p = base / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path() -> Path:
    """Banco gravável do usuário."""
    return user_data_dir() / "equipamentos.db"
