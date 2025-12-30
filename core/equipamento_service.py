# core/equipamento_service.py
from typing import List, Tuple, Optional
from .database import criar_conexao


class EquipamentoService:
    """Serviço para gerenciar tipos e modelos de equipamentos."""

    # ---------- TIPOS ----------
    def listar_tipos(self) -> List[Tuple[int, str]]:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM tipos_equipamento ORDER BY nome;")
        dados = cursor.fetchall()
        conn.close()
        return dados

    def inserir_tipo(self, nome: str) -> int:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tipos_equipamento (nome) VALUES (?);",
            (nome,)
        )
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return novo_id

    def atualizar_tipo(self, tipo_id: int, nome: str) -> None:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tipos_equipamento SET nome = ? WHERE id = ?;",
            (nome, tipo_id)
        )
        conn.commit()
        conn.close()

    def excluir_tipo(self, tipo_id: int) -> None:
        """Exclui o tipo, impedindo exclusão se houver modelos atrelados."""
        conn = criar_conexao()
        cursor = conn.cursor()

        # Verifica se existem modelos usando este tipo
        cursor.execute(
            "SELECT COUNT(*) FROM modelos_equipamento WHERE tipo_id = ?;",
            (tipo_id,)
        )
        qtd = cursor.fetchone()[0]
        if qtd > 0:
            conn.close()
            raise ValueError(
                "Não é possível excluir: existem modelos vinculados a este tipo."
            )

        cursor.execute("DELETE FROM tipos_equipamento WHERE id = ?;", (tipo_id,))
        conn.commit()
        conn.close()

    # ---------- MODELOS ----------
    def listar_modelos(self) -> List[Tuple[int, str, Optional[str], Optional[str]]]:
        """
        Retorna modelos com:
        (id_modelo, nome_modelo, nome_tipo, caminho_imagem)
        """
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                m.id,
                m.nome,
                t.nome AS tipo_nome,
                m.caminho_imagem
            FROM modelos_equipamento m
            LEFT JOIN tipos_equipamento t ON m.tipo_id = t.id
            ORDER BY m.nome;
        """)
        dados = cursor.fetchall()
        conn.close()
        return dados

    def inserir_modelo(self, nome: str, tipo_nome: Optional[str], caminho_imagem: Optional[str]) -> int:
        conn = criar_conexao()
        cursor = conn.cursor()

        tipo_id = None
        if tipo_nome:
            cursor.execute(
                "SELECT id FROM tipos_equipamento WHERE nome = ?;",
                (tipo_nome,)
            )
            row = cursor.fetchone()
            if row:
                tipo_id = row[0]

        cursor.execute("""
            INSERT INTO modelos_equipamento (nome, tipo_id, caminho_imagem)
            VALUES (?, ?, ?);
        """, (nome, tipo_id, caminho_imagem))
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return novo_id

    def atualizar_modelo(self, modelo_id: int, nome: str, tipo_nome: Optional[str], caminho_imagem: Optional[str]) -> None:
        conn = criar_conexao()
        cursor = conn.cursor()

        tipo_id = None
        if tipo_nome:
            cursor.execute(
                "SELECT id FROM tipos_equipamento WHERE nome = ?;",
                (tipo_nome,)
            )
            row = cursor.fetchone()
            if row:
                tipo_id = row[0]

        cursor.execute("""
            UPDATE modelos_equipamento
               SET nome           = ?,
                   tipo_id        = ?,
                   caminho_imagem = ?
             WHERE id = ?;
        """, (nome, tipo_id, caminho_imagem, modelo_id))
        conn.commit()
        conn.close()

    def excluir_modelo(self, modelo_id: int) -> None:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM modelos_equipamento WHERE id = ?;", (modelo_id,))
        conn.commit()
        conn.close()
