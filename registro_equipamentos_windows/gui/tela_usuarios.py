# gui/tela_usuarios.py

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

from core.database import criar_conexao
from .animacoes import aplicar_fade_in, centralizar_janela


class TelaUsuarios(ctk.CTkToplevel):
    def __init__(self, master=None, usuario_logado=None):
        super().__init__(master)

        self.usuario_logado = usuario_logado

        self.title("Gerenciar Usuários")
        self.geometry("900x600")
        self.after(10, lambda: centralizar_janela(self))
        self.after(20, lambda: aplicar_fade_in(self, duracao=300))

        self.minsize(800, 550)

        self._criar_widgets()
        self._carregar_usuarios()

        # fade-in suave
        self.after(10, lambda: aplicar_fade_in(self, duracao=300))

    # ------------------------------------------------------------------ #
    # CRIAÇÃO DOS WIDGETS
    # ------------------------------------------------------------------ #
    def _criar_widgets(self):
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # =================================================================
        # FORMULÁRIO
        # =================================================================
        frame_form = ctk.CTkFrame(container)
        frame_form.pack(fill="x", padx=5, pady=10)

        # ID oculto (para edição)
        self.usuario_id = None

        ctk.CTkLabel(frame_form, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_nome = ctk.CTkEntry(frame_form, width=250)
        self.entry_nome.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_form, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_username = ctk.CTkEntry(frame_form, width=250)
        self.entry_username.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_form, text="Senha:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_senha = ctk.CTkEntry(frame_form, width=250, show="*")
        self.entry_senha.grid(row=2, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_form, text="Perfil:").grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.combo_perfil = ctk.CTkComboBox(
            frame_form,
            values=["ADMIN", "USER"],
            width=120
        )
        self.combo_perfil.set("USER")
        self.combo_perfil.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_form, text="Ativo:").grid(row=1, column=2, padx=5, pady=5, sticky="e")

        self.combo_ativo = ctk.CTkComboBox(
            frame_form,
            values=["1", "0"],  # 1 = ativo, 0 = inativo
            width=120
        )
        self.combo_ativo.set("1")
        self.combo_ativo.grid(row=1, column=3, padx=5, pady=5)

        # Botões de ação
        frame_acoes = ctk.CTkFrame(container)
        frame_acoes.pack(fill="x", pady=5)

        ctk.CTkButton(frame_acoes, text="Salvar", width=120, command=self._salvar_usuario)\
            .pack(side="left", padx=5)

        ctk.CTkButton(frame_acoes, text="Novo", width=120, command=self._limpar_formulario)\
            .pack(side="left", padx=5)

        ctk.CTkButton(frame_acoes, text="Excluir", width=120, fg_color="#A83232",
                      hover_color="#7A2424", command=self._excluir_usuario)\
            .pack(side="left", padx=5)

        ctk.CTkButton(frame_acoes, text="Resetar Senha", width=150,
                      command=self._resetar_senha)\
            .pack(side="left", padx=5)

        btn_sair = ctk.CTkButton(
            frame_acoes, text="Sair", width=120,
            fg_color="#A83232", hover_color="#7A2424",
            command=lambda: self.after(1, self.destroy)
        )
        btn_sair.pack(side="right", padx=5)

        # =================================================================
        # LISTA (TREEVIEW)
        # =================================================================
        frame_lista = ctk.CTkFrame(container)
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        colunas = ("id", "nome", "username", "perfil", "ativo", "criado_em", "atualizado_em")

        self.tree = ttk.Treeview(frame_lista, columns=colunas, show="headings")
        self.tree.pack(fill="both", expand=True)

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("username", text="Usuário")
        self.tree.heading("perfil", text="Perfil")
        self.tree.heading("ativo", text="Ativo")
        self.tree.heading("criado_em", text="Criado em")
        self.tree.heading("atualizado_em", text="Atualizado em")

        for col in colunas:
            self.tree.column(col, width=120, anchor="center")

        self.tree.bind("<<TreeviewSelect>>", self._carregar_para_form)

    # ------------------------------------------------------------------ #
    # CARREGAR LISTA
    # ------------------------------------------------------------------ #
    def _carregar_usuarios(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        con = criar_conexao()
        cursor = con.cursor()

        cursor.execute("""
            SELECT id, nome, username, perfil, ativo, criado_em, atualizado_em
            FROM usuarios
            ORDER BY nome;
        """)

        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)

        con.close()

    # ------------------------------------------------------------------ #
    # CARREGAR PARA FORMULÁRIO
    # ------------------------------------------------------------------ #
    def _carregar_para_form(self, event=None):
        selecao = self.tree.selection()
        if not selecao:
            return

        item = selecao[0]
        valores = self.tree.item(item, "values")

        self.usuario_id = valores[0]
        self.entry_nome.delete(0, "end")
        self.entry_nome.insert(0, valores[1])

        self.entry_username.delete(0, "end")
        self.entry_username.insert(0, valores[2])

        self.combo_perfil.set(valores[3])
        self.combo_ativo.set(str(valores[4]))

        # senha só muda em reset
        self.entry_senha.delete(0, "end")

    # ------------------------------------------------------------------ #
    # LIMPAR FORMULÁRIO
    # ------------------------------------------------------------------ #
    def _limpar_formulario(self):
        self.usuario_id = None
        self.entry_nome.delete(0, "end")
        self.entry_username.delete(0, "end")
        self.entry_senha.delete(0, "end")
        self.combo_perfil.set("USER")
        self.combo_ativo.set("1")

    # ------------------------------------------------------------------ #
    # SALVAR / ATUALIZAR
    # ------------------------------------------------------------------ #
    def _salvar_usuario(self):
        nome = self.entry_nome.get().strip()
        username = self.entry_username.get().strip()
        senha = self.entry_senha.get().strip()
        perfil = self.combo_perfil.get().strip()
        ativo = int(self.combo_ativo.get().strip())

        if not nome or not username:
            messagebox.showwarning("Aviso", "Nome e username são obrigatórios.")
            return

        con = criar_conexao()
        cursor = con.cursor()

        try:
            # INSERIR
            if self.usuario_id is None:
                if not senha:
                    messagebox.showwarning("Aviso", "Senha é obrigatória para novo usuário.")
                    con.close()
                    return

                cursor.execute("""
                    INSERT INTO usuarios
                    (nome, username, senha, perfil, ativo)
                    VALUES (?, ?, ?, ?, ?)
                """, (nome, username, senha, perfil, ativo))

            # ATUALIZAR
            else:
                cursor.execute("""
                    UPDATE usuarios
                    SET nome=?, username=?, perfil=?, ativo=?, atualizado_em=datetime('now')
                    WHERE id=?
                """, (nome, username, perfil, ativo, self.usuario_id))

                if senha:
                    cursor.execute("""
                        UPDATE usuarios
                        SET senha=?, atualizado_em=datetime('now')
                        WHERE id=?
                    """, (senha, self.usuario_id))

            con.commit()
            messagebox.showinfo("Sucesso", "Usuário salvo com sucesso!")
            self._limpar_formulario()
            self._carregar_usuarios()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar usuário:\n{e}")
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # EXCLUIR
    # ------------------------------------------------------------------ #
    def _excluir_usuario(self):
        if not self.usuario_id:
            messagebox.showwarning("Aviso", "Selecione um usuário.")
            return

        # impedir excluir o próprio usuário
        if str(self.usuario_id) == str(self.usuario_logado.get("id")):
            messagebox.showwarning("Aviso", "Você não pode excluir seu próprio usuário.")
            return

        if not messagebox.askyesno("Confirmar", "Deseja realmente excluir este usuário?"):
            return

        con = criar_conexao()
        cursor = con.cursor()

        try:
            cursor.execute("DELETE FROM usuarios WHERE id=?", (self.usuario_id,))
            con.commit()

            messagebox.showinfo("Sucesso", "Usuário excluído!")
            self._limpar_formulario()
            self._carregar_usuarios()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir usuário:\n{e}")
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # RESETAR SENHA
    # ------------------------------------------------------------------ #
    def _resetar_senha(self):
        if not self.usuario_id:
            messagebox.showwarning("Aviso", "Selecione um usuário.")
            return

        nova = "123456"

        con = criar_conexao()
        cursor = con.cursor()

        try:
            cursor.execute("""
                UPDATE usuarios
                SET senha=?, atualizado_em=datetime('now')
                WHERE id=?
            """, (nova, self.usuario_id))

            con.commit()
            messagebox.showinfo("Sucesso", f"Senha redefinida para: {nova}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao redefinir senha:\n{e}")
        finally:
            con.close()
