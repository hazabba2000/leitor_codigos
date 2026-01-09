# core/database.py
from __future__ import annotations

from pathlib import Path
import os
import sys
import shutil
import sqlite3


APP_NAME = "leitor_codigos"       # Linux
APP_NAME_WIN = "LeitorCodigos"    # Windows (pasta em AppData)


def _resource_path(rel: str) -> Path:
    """
    Caminho para arquivos empacotados (PyInstaller) ou no modo dev.
    - Dev: raiz do projeto
    - PyInstaller: sys._MEIPASS
    """
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent.parent  # raiz do projeto
    return base / rel


def _user_data_dir() -> Path:
    """
    Pasta gravável do usuário.
    - Windows: %LOCALAPPDATA%\LeitorCodigos
    - Linux: XDG_DATA_HOME ou ~/.local/share/leitor_codigos
    """
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        p = base / APP_NAME_WIN
        p.mkdir(parents=True, exist_ok=True)
        return p

    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else (Path.home() / ".local" / "share")
    p = base / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def _db_path() -> Path:
    """Banco gravável do usuário."""
    return _user_data_dir() / "equipamentos.db"


def _garantir_banco_no_usuario():
    """
    Se o banco não existir no local gravável do usuário,
    copia o banco modelo (empacotado junto) para lá.
    """
    destino = _db_path()
    if destino.exists():
        return

    origem = _resource_path("equipamentos_template.db")  # template empacotado
    if origem.exists():
        try:
            shutil.copy2(origem, destino)
            return
        except Exception:
            pass

    # fallback: cria vazio (será inicializado com tabelas/seeds depois)
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.touch(exist_ok=True)
    except Exception:
        pass


def criar_conexao() -> sqlite3.Connection:
    _garantir_banco_no_usuario()
    conn = sqlite3.connect(_db_path(), timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_banco():
    """Cria as tabelas necessárias e carrega dados padrões (apenas na primeira vez)."""
    conn = criar_conexao()
    cursor = conn.cursor()

    # Tabela principal de registros
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_serie     TEXT NOT NULL,
            status           TEXT,
            tipo_equipamento TEXT,
            modelo           TEXT,
            agente           TEXT,
            data_saida       TEXT,
            data_retorno     TEXT,
            quantidade       INTEGER
        );
    """)

    # Tabela de tipos de equipamento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_equipamento (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        );
    """)

    # Tabela de modelos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modelos_equipamento (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nome           TEXT UNIQUE NOT NULL,
            tipo_id        INTEGER,
            caminho_imagem TEXT,
            FOREIGN KEY (tipo_id) REFERENCES tipos_equipamento(id)
        );
    """)

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nome     TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            senha    TEXT NOT NULL,
            perfil   TEXT DEFAULT 'OPERADOR'
        );
    """)

    # Configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT
        );
    """)

    # Auditoria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_auditoria (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tabela      TEXT NOT NULL,
            registro_id INTEGER,
            acao        TEXT NOT NULL,
            detalhes    TEXT,
            usuario     TEXT,
            criado_em   TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    # Migração perfil
    cursor.execute("PRAGMA table_info(usuarios);")
    colunas = [row[1] for row in cursor.fetchall()]
    if "perfil" not in colunas:
        try:
            cursor.execute(
                "ALTER TABLE usuarios ADD COLUMN perfil TEXT DEFAULT 'OPERADOR';"
            )
        except sqlite3.OperationalError:
            pass

    # Bootstrap admin (UMA VEZ)
    cursor.execute("""
        SELECT 1 FROM configuracoes
         WHERE chave = 'bootstrap_admin_v1'
         LIMIT 1;
    """)
    ja_rodou = cursor.fetchone()

    if not ja_rodou:
        cursor.execute("""
            INSERT OR REPLACE INTO usuarios (id, nome, username, senha, perfil)
            VALUES (
                1,
                'Administrador',
                'admin',
                '$pbkdf2-sha256$29000$W6sVorS2ttY6p7TWGmOsFQ$vW1bLKo13KvmXNdfooX6gr6bkhPmMG3pLlPWQxHXwA0',
                'ADMIN'
            );
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO configuracoes (chave, valor)
            VALUES ('bootstrap_admin_v1', '1');
        """)

    cursor.execute("""
        UPDATE usuarios
           SET perfil = 'ADMIN'
         WHERE username = 'admin';
    """)

    cursor.execute("""
        UPDATE usuarios
           SET perfil = 'OPERADOR'
         WHERE username <> 'admin' AND (perfil IS NULL OR perfil = '');
    """)

    conn.commit()
    conn.close()
