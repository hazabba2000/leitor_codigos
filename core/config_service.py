# core/config_service.py
from typing import Optional
import os

from .database import criar_conexao, inicializar_banco


class ConfigService:
    """Serviço para guardar e recuperar configurações gerais do sistema."""

    def __init__(self):
        # garante que tabelas existam
        inicializar_banco()

    def _get_valor(self, chave: str) -> Optional[str]:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT valor FROM configuracoes WHERE chave = ?;",
            (chave,)
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def _set_valor(self, chave: str, valor: str) -> None:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO configuracoes (chave, valor)
            VALUES (?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor;
        """, (chave, valor))
        conn.commit()
        conn.close()

    # ---------- Tema (claro/escuro) ----------

    def detectar_tema_sistema(self) -> str:
        """
        Tentativa simples de detectar tema do sistema.
        Se encontrar 'dark' em GTK_THEME, usa 'dark'. Caso contrário, 'light'.
        """
        gtk_theme = os.getenv("GTK_THEME", "").lower()
        if "dark" in gtk_theme:
            return "dark"
        # fallback: claro
        return "light"

    def obter_tema_preferido(self) -> str:
        """
        Retorna 'dark' ou 'light'.
        Se não houver nada salvo, detecta do sistema e salva.
        """
        valor = self._get_valor("tema")
        if valor in ("dark", "light"):
            return valor

        tema = self.detectar_tema_sistema()
        self._set_valor("tema", tema)
        return tema

    def salvar_tema(self, tema: str) -> None:
        """
        Salva 'dark' ou 'light' como tema preferido.
        """
        if tema not in ("dark", "light"):
            return
        self._set_valor("tema", tema)
