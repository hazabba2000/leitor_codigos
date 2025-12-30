# gui/tela_logs.py

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry

from core.database import criar_conexao
from .animacoes import aplicar_fade_in, centralizar_janela


class TelaLogs(ctk.CTkToplevel):
    def __init__(self, master=None, usuario_logado=None):
        super().__init__(master)

        self.usuario_logado = usuario_logado

        self.title("Logs de Auditoria")
        self.geometry("1000x600")
        self.minsize(900, 500)

        # Centralizar e fade-in
        self.after(10, lambda: centralizar_janela(self))
        self.after(20, lambda: aplicar_fade_in(self, duracao=300))

        self._criar_widgets()
        self._carregar_usuarios_filtro()
        self._carregar_logs()  # carrega tudo inicialmente

    # ------------------------------------------------------------------ #
    # CRIAÇÃO DA INTERFACE
    # ------------------------------------------------------------------ #
    def _criar_widgets(self):
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # ================================================================
        # BARRA DE FILTRO
        # ================================================================
        frame_filtros = ctk.CTkFrame(container)
        frame_filtros.pack(fill="x", padx=5, pady=(5, 10))

        # Usuário
        lbl_usuario = ctk.CTkLabel(frame_filtros, text="Usuário:")
        lbl_usuario.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.combo_usuario = ctk.CTkComboBox(
            frame_filtros,
            values=["Todos"],
            width=160,
        )
        self.combo_usuario.set("Todos")
        self.combo_usuario.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Tipo de ação
        lbl_acao = ctk.CTkLabel(frame_filtros, text="Ação:")
        lbl_acao.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.combo_acao = ctk.CTkComboBox(
            frame_filtros,
            values=["Todos", "INSERT", "UPDATE", "DELETE"],
            width=140,
        )
        self.combo_acao.set("Todos")
        self.combo_acao.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Data inicial
        lbl_data_ini = ctk.CTkLabel(frame_filtros, text="Data Inicial:")
        lbl_data_ini.grid(row=1, column=0, padx=5, pady=5, sticky="e")

        self.date_ini = DateEntry(
            frame_filtros,
            date_pattern="dd/mm/yyyy",
            width=12
        )
        self.date_ini.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        # limpa para deixar opcional
        self.date_ini.delete(0, "end")

        # Data final
        lbl_data_fim = ctk.CTkLabel(frame_filtros, text="Data Final:")
        lbl_data_fim.grid(row=1, column=2, padx=5, pady=5, sticky="e")

        self.date_fim = DateEntry(
            frame_filtros,
            date_pattern="dd/mm/yyyy",
            width=12
        )
        self.date_fim.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.date_fim.delete(0, "end")

        # Botões filtro
        frame_botoes = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        frame_botoes.grid(row=0, column=4, rowspan=2, padx=10, pady=5, sticky="ns")

        btn_aplicar = ctk.CTkButton(
            frame_botoes,
            text="Aplicar Filtro",
            width=130,
            command=self._aplicar_filtro
        )
        btn_aplicar.pack(padx=5, pady=3)

        btn_limpar = ctk.CTkButton(
            frame_botoes,
            text="Limpar Filtros",
            width=130,
            command=self._limpar_filtros
        )
        btn_limpar.pack(padx=5, pady=3)

        btn_fechar = ctk.CTkButton(
            frame_botoes,
            text="Fechar",
            width=130,
            fg_color="#A83232",
            hover_color="#7A2424",
            command=lambda: self.after(1, self.destroy)
        )
        btn_fechar.pack(padx=5, pady=(8, 3))

        # ================================================================
        # LISTA (TREEVIEW)
        # ================================================================
        frame_lista = ctk.CTkFrame(container)
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        colunas = ("id", "criado_em", "usuario", "tabela", "registro_id", "acao", "detalhes")

        self.tree = ttk.Treeview(frame_lista, columns=colunas, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.heading("id", text="ID")
        self.tree.heading("criado_em", text="Data/Hora")
        self.tree.heading("usuario", text="Usuário")
        self.tree.heading("tabela", text="Tabela")
        self.tree.heading("registro_id", text="Registro ID")
        self.tree.heading("acao", text="Ação")
        self.tree.heading("detalhes", text="Detalhes")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("criado_em", width=150, anchor="center")
        self.tree.column("usuario", width=140, anchor="center")
        self.tree.column("tabela", width=120, anchor="center")
        self.tree.column("registro_id", width=90, anchor="center")
        self.tree.column("acao", width=80, anchor="center")
        self.tree.column("detalhes", width=380, anchor="w")

        scroll = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

    # ------------------------------------------------------------------ #
    # CARREGAR OPÇÕES DE USUÁRIO PARA FILTRO
    # ------------------------------------------------------------------ #
    def _carregar_usuarios_filtro(self):
        try:
            con = criar_conexao()
            cur = con.cursor()
            cur.execute("""
                SELECT DISTINCT usuario
                  FROM logs_auditoria
                 WHERE usuario IS NOT NULL AND usuario <> ''
                 ORDER BY usuario;
            """)
            usuarios = [row[0] for row in cur.fetchall()]
            con.close()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar usuários de logs:\n{e}")
            usuarios = []

        valores = ["Todos"]
        valores.extend(usuarios)

        self.combo_usuario.configure(values=valores)
        self.combo_usuario.set("Todos")

    # ------------------------------------------------------------------ #
    # CARREGAR LOGS COM OU SEM FILTRO
    # ------------------------------------------------------------------ #
    def _carregar_logs(self, usuario=None, acao=None,
                       data_ini_sql=None, data_fim_sql=None):
        # Limpa a lista
        for item in self.tree.get_children():
            self.tree.delete(item)

        query = """
            SELECT id, criado_em, usuario, tabela, registro_id, acao, detalhes
              FROM logs_auditoria
             WHERE 1=1
        """
        params = []

        if usuario:
            query += " AND usuario = ?"
            params.append(usuario)

        if acao:
            query += " AND acao = ?"
            params.append(acao)

        if data_ini_sql:
            query += " AND criado_em >= ?"
            params.append(data_ini_sql)

        if data_fim_sql:
            query += " AND criado_em <= ?"
            params.append(data_fim_sql)

        query += " ORDER BY criado_em DESC, id DESC"

        try:
            con = criar_conexao()
            cur = con.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            con.close()

            for row in rows:
                self.tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar logs:\n{e}")

    # ------------------------------------------------------------------ #
    # APLICAR FILTRO
    # ------------------------------------------------------------------ #
    def _aplicar_filtro(self):
        usuario = self.combo_usuario.get().strip()
        acao = self.combo_acao.get().strip()

        if usuario == "Todos":
            usuario = None
        if acao == "Todos":
            acao = None

        data_ini_txt = self.date_ini.get().strip()
        data_fim_txt = self.date_fim.get().strip()

        data_ini_sql = None
        data_fim_sql = None

        # Converte dd/mm/yyyy -> yyyy-mm-dd HH:MM:SS
        try:
            if data_ini_txt:
                dt_ini = datetime.strptime(data_ini_txt, "%d/%m/%Y")
                data_ini_sql = dt_ini.strftime("%Y-%m-%d 00:00:00")
            if data_fim_txt:
                dt_fim = datetime.strptime(data_fim_txt, "%d/%m/%Y")
                data_fim_sql = dt_fim.strftime("%Y-%m-%d 23:59:59")
        except ValueError:
            messagebox.showwarning("Aviso", "Data inválida. Use o formato dd/mm/aaaa.")
            return

        self._carregar_logs(usuario=usuario, acao=acao,
                            data_ini_sql=data_ini_sql, data_fim_sql=data_fim_sql)

    # ------------------------------------------------------------------ #
    # LIMPAR FILTROS
    # ------------------------------------------------------------------ #
    def _limpar_filtros(self):
        self.combo_usuario.set("Todos")
        self.combo_acao.set("Todos")
        self.date_ini.delete(0, "end")
        self.date_fim.delete(0, "end")
        self._carregar_logs()
