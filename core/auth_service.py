# core/auth_service.py
from typing import Optional, Dict
from .database import criar_conexao, inicializar_banco


class AuthService:
    """Serviço de autenticação."""

    def __init__(self):
        # garante que o banco/tabelas existam
        inicializar_banco()

    def autenticar(self, username: str, senha: str) -> Optional[Dict]:
        """
        Retorna um dict com:
        { id, nome, username, perfil }
        ou None se usuário/senha inválidos.
        """
        conn = criar_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome, username, perfil
              FROM usuarios
             WHERE username = ? AND senha = ?;
        """, (username, senha))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "nome": row[1],
            "username": row[2],
            "perfil": row[3] or "OPERADOR",
        }

