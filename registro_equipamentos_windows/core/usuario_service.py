# core/usuario_service.py
from typing import List, Tuple, Optional
import sqlite3

from .database import criar_conexao


class UsuarioService:
    """CRUD de usuários."""

    def listar_usuarios(self) -> List[Tuple[int, str, str, str]]:
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome, username, perfil
              FROM usuarios
             ORDER BY nome;
        """)
        dados = cursor.fetchall()
        conn.close()
        return dados

    def criar_usuario(self, nome: str, username: str, senha: str, perfil: str) -> int:
        conn = criar_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO usuarios (nome, username, senha, perfil)
                VALUES (?, ?, ?, ?);
            """, (nome, username, senha, perfil))
            conn.commit()
            novo_id = cursor.lastrowid
        except sqlite3.IntegrityError as e:
            conn.close()
            raise ValueError("Já existe um usuário com esse username.") from e
        conn.close()
        return novo_id

    def atualizar_usuario(
        self,
        usuario_id: int,
        nome: str,
        username: str,
        perfil: str,
        senha: Optional[str] = None,
    ) -> None:
        conn = criar_conexao()
        cursor = conn.cursor()

        try:
            if senha:
                cursor.execute("""
                    UPDATE usuarios
                       SET nome = ?,
                           username = ?,
                           senha = ?,
                           perfil = ?
                     WHERE id = ?;
                """, (nome, username, senha, perfil, usuario_id))
            else:
                cursor.execute("""
                    UPDATE usuarios
                       SET nome = ?,
                           username = ?,
                           perfil = ?
                     WHERE id = ?;
                """, (nome, username, perfil, usuario_id))
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.close()
            raise ValueError("Já existe um usuário com esse username.") from e

        conn.close()

    def excluir_usuario(self, usuario_id: int) -> None:
        """Não permite excluir o admin (id=1)."""
        if usuario_id == 1:
            raise ValueError("O usuário 'admin' não pode ser excluído.")

        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = ?;", (usuario_id,))
        conn.commit()
        conn.close()
