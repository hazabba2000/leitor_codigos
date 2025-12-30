# core/dashboard_service.py
from typing import Dict, List, Tuple
from .database import criar_conexao


class DashboardService:
    """Serviço para consultas agregadas do Dashboard."""

    def _fetchone_int(self, cursor, query: str, params=()) -> int:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def obter_resumo_geral(self) -> Dict[str, int]:
        """
        Retorna:
        - total_registros: quantidade de linhas na tabela
        - total_quantidade: soma da coluna quantidade
        - total_good / total_bad / total_manutencao: por status
        """
        conn = criar_conexao()
        cursor = conn.cursor()

        total_registros = self._fetchone_int(cursor, "SELECT COUNT(*) FROM registros;")
        total_quantidade = self._fetchone_int(cursor, "SELECT COALESCE(SUM(quantidade), 0) FROM registros;")

        total_good = self._fetchone_int(
            cursor,
            "SELECT COALESCE(SUM(quantidade), 0) FROM registros WHERE status = 'GOOD';"
        )
        total_bad = self._fetchone_int(
            cursor,
            "SELECT COALESCE(SUM(quantidade), 0) FROM registros WHERE status = 'BAD';"
        )
        total_manutencao = self._fetchone_int(
            cursor,
            "SELECT COALESCE(SUM(quantidade), 0) FROM registros WHERE status = 'EM MANUTENÇÃO';"
        )

        conn.close()

        return {
            "total_registros": total_registros,
            "total_quantidade": total_quantidade,
            "total_good": total_good,
            "total_bad": total_bad,
            "total_manutencao": total_manutencao,
        }

    def obter_totais_por_tipo(self) -> List[Tuple[str, int]]:
        """Retorna lista (tipo_equipamento, soma_quantidade)."""
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(tipo_equipamento, 'SEM TIPO') AS tipo,
                COALESCE(SUM(quantidade), 0) AS total
            FROM registros
            GROUP BY tipo
            ORDER BY total DESC;
        """)
        dados = [(row[0], int(row[1])) for row in cursor.fetchall()]
        conn.close()
        return dados

    def obter_totais_por_agente(self) -> List[Tuple[str, int]]:
        """Retorna lista (agente, soma_quantidade)."""
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(agente, 'SEM AGENTE') AS agente,
                COALESCE(SUM(quantidade), 0) AS total
            FROM registros
            GROUP BY agente
            ORDER BY total DESC;
        """)
        dados = [(row[0], int(row[1])) for row in cursor.fetchall()]
        conn.close()
        return dados
