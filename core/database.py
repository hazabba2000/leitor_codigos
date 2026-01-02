# core/database.py
from __future__ import annotations

from pathlib import Path
import os
import sys
import shutil
import sqlite3


APP_NAME = "leitor_codigos"


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
    Preferência: XDG_DATA_HOME; senão ~/.local/share
    """
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

    origem = _resource_path("equipamentos_template.db")  # <- 2) aponta para o template empacotado
    # Se você empacotar sem o arquivo, ainda funciona criando do zero (só tabelas + seeds)
    return _user_data_dir() / "equipamentos.db"          # <- 3) mantém o DB real no local gravável
    if origem.exists():
        try:
            shutil.copy2(origem, destino)
        except Exception:
            # fallback: cria vazio (será inicializado com tabelas/seeds depois)
            pass


def criar_conexao() -> sqlite3.Connection:
    _garantir_banco_no_usuario()
    conn = sqlite3.connect(_db_path())
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

    # Tabela de modelos (com caminho da imagem)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modelos_equipamento (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            nome           TEXT UNIQUE NOT NULL,
            tipo_id        INTEGER,
            caminho_imagem TEXT,
            FOREIGN KEY (tipo_id) REFERENCES tipos_equipamento(id)
        );
    """)

    # Tabela de usuários (login) – já com coluna perfil
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nome     TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            senha    TEXT NOT NULL,
            perfil   TEXT DEFAULT 'OPERADOR'
        );
    """)

    # Tabela de configurações gerais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT
        );
    """)

    # Tabela de logs / auditoria
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

    # --- MIGRAÇÃO: garante que a coluna 'perfil' exista em bancos antigos ---
    cursor.execute("PRAGMA table_info(usuarios);")
    colunas = [row[1] for row in cursor.fetchall()]
    if "perfil" not in colunas:
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN perfil TEXT DEFAULT 'OPERADOR';")
        except sqlite3.OperationalError:
            pass

    # --------- DADOS PADRÃO (APENAS SE A TABELA ESTIVER VAZIA) ---------

    # Tipos de equipamento
    tipos_padrao = ["SMART POS", "GPRS-WIFI", "BLUETOOTH-GPRS"]

    cursor.execute("SELECT COUNT(*) FROM tipos_equipamento;")
    qtd_tipos = cursor.fetchone()[0]

    if qtd_tipos == 0:
        cursor.executemany(
            "INSERT INTO tipos_equipamento (nome) VALUES (?);",
            [(nome,) for nome in tipos_padrao]
        )

    # Atualiza o mapa de tipos (já com o que estiver no banco)
    cursor.execute("SELECT id, nome FROM tipos_equipamento;")
    tipos = {nome: _id for _id, nome in cursor.fetchall()}

    # Modelos de equipamento
    modelos_padrao = [
        ("P2-A11",   "SMART POS",      "equipamentos/P2A11.png"),
        ("D-188",    "BLUETOOTH-GPRS", "equipamentos/D188.png"),
        ("D230",     "GPRS-WIFI",      "equipamentos/D230.png"),
        ("MP35P-ST", "GPRS-WIFI",      "equipamentos/MP35P-ST.png"),
    ]

    cursor.execute("SELECT COUNT(*) FROM modelos_equipamento;")
    qtd_modelos = cursor.fetchone()[0]

    if qtd_modelos == 0:
        for nome_modelo, nome_tipo, caminho in modelos_padrao:
            tipo_id = tipos.get(nome_tipo) if nome_tipo else None
            cursor.execute("""
                INSERT INTO modelos_equipamento
                    (nome, tipo_id, caminho_imagem)
                VALUES (?, ?, ?);
            """, (nome_modelo, tipo_id, caminho))

    # --- MIGRAÇÃO: normaliza caminhos antigos "assets/equipamentos/..." -> "equipamentos/..."
    try:
        cursor.execute("""
            UPDATE modelos_equipamento
            SET caminho_imagem = REPLACE(caminho_imagem, 'assets/equipamentos/', 'equipamentos/')
            WHERE caminho_imagem LIKE 'assets/equipamentos/%';
        """)
    except sqlite3.OperationalError:
        pass


    # Usuário padrão: admin / admin (perfil ADMIN)
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id, nome, username, senha, perfil)
        VALUES (1, 'Administrador', 'admin', 'admin', 'ADMIN');
    """)

    # Garante que o admin SEMPRE tenha perfil ADMIN
    cursor.execute("""
        UPDATE usuarios
           SET perfil = 'ADMIN'
         WHERE username = 'admin';
    """)

    # Demais usuários sem perfil viram OPERADOR
    cursor.execute("""
        UPDATE usuarios
           SET perfil = 'OPERADOR'
         WHERE username <> 'admin' AND (perfil IS NULL OR perfil = '');
    """)

    conn.commit()
    conn.close()



