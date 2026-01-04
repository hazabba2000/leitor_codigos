# core/bootstrap_admin.py
import os
import sys
import shutil
import sqlite3
from pathlib import Path
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def _local_appdata_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        # fallback (raro)
        return Path.home() / "AppData" / "Local"
    return Path(local)


def _user_db_path() -> Path:
    return _local_appdata_dir() / "LeitorCodigos" / "equipamentos.db"


def _template_candidates() -> list[Path]:
    base = _local_appdata_dir() / "LeitorCodigos"
    internal = base / "_internal"

    candidates: list[Path] = [
        # 1) template já instalado pelo Setup (o seu caso no Windows)
        internal / "equipamentos_template.db",
        internal / "equipamentos_template",
        internal / "equipamentos_template.sqlite",
        internal / "equipamentos_template.sqlite3",

        # 2) template solto na pasta do app (caso exista)
        base / "equipamentos_template.db",
        base / "equipamentos_template",
    ]

    # 3) PyInstaller (arquivos extraídos em runtime)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        mp = Path(meipass)
        candidates += [
            mp / "equipamentos_template.db",
            mp / "equipamentos_template",
            mp / "equipamentos_template.sqlite",
            mp / "equipamentos_template.sqlite3",
        ]

    # 4) desenvolvimento (rodando do repo)
    here = Path(__file__).resolve()
    repo_root = here.parents[1]
    candidates += [
        repo_root / "data" / "equipamentos_template.db",
        repo_root / "data" / "equipamentos_template",
        repo_root / "equipamentos_template.db",
        repo_root / "equipamentos_template",
    ]

    return candidates


def _find_template() -> Path | None:
    for p in _template_candidates():
        if p.exists() and p.is_file():
            return p
    return None


def _table_exists(cur: sqlite3.Cursor, name: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _columns(cur: sqlite3.Cursor, table: str) -> list[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def _ensure_admin(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    if not _table_exists(cur, "usuarios"):
        # Se seu app cria as tabelas em outro momento, não faz nada aqui.
        return

    cols = _columns(cur, "usuarios")

    user_col = next((c for c in ["login", "username", "usuario", "user", "email"] if c in cols), None)
    pass_col = next((c for c in ["senha", "password", "senha_hash", "hash_senha"] if c in cols), None)

    if not user_col or not pass_col:
        return

    admin_hash = _pwd.hash("admin")

    # tenta atualizar
    cur.execute(f"UPDATE usuarios SET {pass_col}=? WHERE {user_col}='admin'", (admin_hash,))
    conn.commit()

    # se não existe, cria preenchendo campos obrigatórios comuns
    if cur.rowcount == 0:
        insert_cols = [user_col, pass_col]
        insert_vals = ["admin", admin_hash]

        if "nome" in cols:
            insert_cols.append("nome")
            insert_vals.append("Administrador")

        if "perfil" in cols:
            insert_cols.append("perfil")
            insert_vals.append("ADMIN")

        placeholders = ", ".join(["?"] * len(insert_cols))
        sql = f"INSERT INTO usuarios ({', '.join(insert_cols)}) VALUES ({placeholders})"
        cur.execute(sql, insert_vals)
        conn.commit()


def bootstrap_default_admin() -> Path:
    """
    1) Garante que existe um banco gravável: %LOCALAPPDATA%\\LeitorCodigos\\equipamentos.db
       - Se não existir, copia do template empacotado
    2) Garante usuário admin/admin dentro do equipamentos.db
    """
    db_path = _user_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        tpl = _find_template()
        if tpl:
            shutil.copy2(tpl, db_path)
        else:
            # Se não achar template, cria um banco vazio (o app pode criar as tabelas depois)
            db_path.touch()

    # agora tenta garantir admin
    conn = sqlite3.connect(db_path)
    try:
        _ensure_admin(conn)
    finally:
        conn.close()

    return db_path
