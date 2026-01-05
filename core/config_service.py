# core/config_service.py
from __future__ import annotations

import sqlite3
from .database import criar_conexao



class ConfigService:
    def __init__(self):
        pass

    def _garantir_tabela(self, cur: sqlite3.Cursor):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT
            );
        """)

    def _get_valor(self, chave: str) -> str | None:
        conn = criar_conexao()
        cur = conn.cursor()
        self._garantir_tabela(cur)
        cur.execute("SELECT valor FROM configuracoes WHERE chave=? LIMIT 1;", (chave,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None

    def obter_tema_preferido(self) -> str:
        # ✅ Não grava nada no banco no start (evita lock)
        tema = self._get_valor("tema")
        return tema if tema else "system"


