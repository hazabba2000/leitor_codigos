# web_app/database.py
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "equipamentos.db"


def criar_conexao():
    return sqlite3.connect(DB_PATH)


def listar_registros():
    """Retorna todos os registros como lista de tuplas."""
    con = criar_conexao()
    cur = con.cursor()
    cur.execute(
        """
        SELECT
            id,
            numero_serie,
            status,
            tipo_equipamento,
            modelo,
            agente,
            quantidade,
            data_saida,
            data_retorno
        FROM registros
        ORDER BY id DESC;
        """
    )
    rows = cur.fetchall()
    con.close()
    return rows


def listar_tipos():
    """Lista tipos da tabela tipos_equipamento (ou vazio se não tiver)."""
    con = criar_conexao()
    cur = con.cursor()
    try:
        cur.execute("SELECT nome FROM tipos_equipamento ORDER BY nome;")
        rows = [r[0] for r in cur.fetchall()]
    except Exception:
        rows = []
    con.close()
    return rows


def listar_modelos():
    """Lista modelos da tabela modelos_equipamento (ou vazio se não tiver)."""
    con = criar_conexao()
    cur = con.cursor()
    try:
        cur.execute("SELECT nome FROM modelos_equipamento ORDER BY nome;")
        rows = [r[0] for r in cur.fetchall()]
    except Exception:
        rows = []
    con.close()
    return rows


def inserir_registro(numero_serie, status, tipo, modelo, agente,
                     data_saida, data_retorno, quantidade: int):
    """Insere um registro na tabela registros."""
    con = criar_conexao()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO registros
            (numero_serie, status, tipo_equipamento, modelo,
             agente, data_saida, data_retorno, quantidade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (numero_serie, status, tipo, modelo, agente,
         data_saida or None, data_retorno or None, quantidade),
    )
    con.commit()
    new_id = cur.lastrowid
    con.close()
    return new_id
