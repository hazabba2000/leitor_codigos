# core/audit_service.py

from typing import Optional
from .database import criar_conexao


class AuditService:
    """Serviço responsável por registrar logs de auditoria no banco."""

    def registrar(
        self,
        tabela: str,
        acao: str,
        registro_id: Optional[int] = None,
        detalhes: Optional[str] = None,
        usuario: Optional[str] = None,
    ) -> None:
        """
        tabela      -> nome lógico da tabela (ex.: 'registros')
        acao        -> 'INSERT', 'UPDATE', 'DELETE', etc.
        registro_id -> id do registro afetado (quando houver)
        detalhes    -> texto livre (ex.: campos alterados)
        usuario     -> username de quem executou a ação
        """
        con = criar_conexao()
        cur = con.cursor()

        cur.execute(
            """
            INSERT INTO logs_auditoria (tabela, registro_id, acao, detalhes, usuario)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tabela, registro_id, acao, detalhes, usuario),
        )

        con.commit()
        con.close()
