from pathlib import Path
import shutil
import sys
import os

APP_NAME = "LeitorCodigos"


def get_app_data_dir() -> Path:
    """Retorna diretório gravável do usuário"""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"

    app_dir = base / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_db_path() -> Path:
    return get_app_data_dir() / "equipamentos.db"


def get_template_path() -> Path:
    """
    Caminho do template dentro do pacote (PyInstaller)
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "data" / "equipamentos_template.db"
    return Path("data") / "equipamentos_template.db"


def ensure_db_exists() -> Path:
    db_path = get_db_path()
    if not db_path.exists():
        template = get_template_path()
        if not template.exists():
            raise FileNotFoundError(f"Template não encontrado: {template}")

        shutil.copy(template, db_path)

    return db_path
