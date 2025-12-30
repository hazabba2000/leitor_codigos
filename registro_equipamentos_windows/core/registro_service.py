# core/registro_service.py
from typing import List, Tuple, Optional
from .database import criar_conexao
from pathlib import Path
from core.paths import asset_path


class RegistroService:
    """Camada de serviço: fala com o banco e devolve dados para a GUI."""

    # ------------------- REGISTROS -------------------
    def listar_registros(self) -> List[Tuple]:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
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
        """)
        dados = cursor.fetchall()
        conn.close()
        return dados

    def filtrar_por_numero_serie(self, termo: str) -> List[Tuple]:
        conn = criar_conexao()
        cursor = conn.cursor()
        like = f"%{termo}%"
        cursor.execute("""
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
            WHERE numero_serie LIKE ?
            ORDER BY id DESC;
        """, (like,))
        dados = cursor.fetchall()
        conn.close()
        return dados

    def inserir_registro(
        self,
        numero_serie: str,
        status: str,
        tipo_equipamento: str,
        modelo: str,
        agente: str,
        data_saida: str,
        data_retorno: str,
        quantidade: int,
    ) -> int:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registros (
                numero_serie,
                status,
                tipo_equipamento,
                modelo,
                agente,
                data_saida,
                data_retorno,
                quantidade
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            numero_serie, status, tipo_equipamento, modelo,
            agente, data_saida, data_retorno, quantidade
        ))
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return novo_id

    def atualizar_registro(
        self,
        id_registro: int,
        numero_serie: str,
        status: str,
        tipo_equipamento: str,
        modelo: str,
        agente: str,
        data_saida: str,
        data_retorno: str,
        quantidade: int,
    ) -> None:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE registros
               SET numero_serie     = ?,
                   status           = ?,
                   tipo_equipamento = ?,
                   modelo           = ?,
                   agente           = ?,
                   data_saida       = ?,
                   data_retorno     = ?,
                   quantidade       = ?
             WHERE id = ?;
        """, (
            numero_serie, status, tipo_equipamento, modelo,
            agente, data_saida, data_retorno, quantidade, id_registro
        ))
        conn.commit()
        conn.close()

    def excluir_registro(self, id_registro: int) -> None:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registros WHERE id = ?;", (id_registro,))
        conn.commit()
        conn.close()

    # ------------------- TIPOS / MODELOS -------------------
    def listar_tipos_equipamento(self) -> List[str]:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM tipos_equipamento ORDER BY nome;")
        dados = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dados

    def listar_modelos(self) -> List[str]:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM modelos_equipamento ORDER BY nome;")
        dados = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dados

    def obter_caminho_imagem_modelo(self, nome_modelo: str) -> Optional[str]:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT caminho_imagem FROM modelos_equipamento WHERE nome = ?;",
            (nome_modelo,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            return None

        caminho = str(row[0]).strip()
        p = Path(caminho)

        # Absoluto? devolve como está
        if p.is_absolute():
            return str(p)

        parts = p.parts

        # Se veio com "assets/...", remove "assets/" e resolve dentro de assets/
        if "assets" in parts:
            idx = parts.index("assets")
            rel = Path(*parts[idx + 1:])  # ex: equipamentos/D188.png
            return str(asset_path(*rel.parts))

        # Se veio só "D188.png", assume assets/equipamentos/D188.png
        if len(parts) == 1:
            return str(asset_path("equipamentos", parts[0]))

        # Se veio "equipamentos/D188.png" ou similar
        return str(asset_path(*parts))




