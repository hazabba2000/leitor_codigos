# gui/tela_dashboard.py

import customtkinter as ctk
from tkinter import ttk
from tkcalendar import DateEntry
from collections import Counter
from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.registro_service import RegistroService
from gui.animacoes import aplicar_fade_in, centralizar_janela



class TelaDashboard(ctk.CTkToplevel):
    def __init__(self, master=None, service: RegistroService | None = None):
        super().__init__(master)

        self.title("Dashboard / Estatísticas")
        self.geometry("1200x700")
        self.after(10, lambda: centralizar_janela(self))
        self.after(20, lambda: aplicar_fade_in(self, duracao=300))

        self.minsize(900, 600)

        self.service = service or RegistroService()
        self.registros = []
        self.registros_filtrados = []

        # widgets
        self.entry_data_inicio = None
        self.entry_data_fim = None
        self.combo_status = None
        self.combo_agente = None

        # cards
        self.lbl_total = None
        self.lbl_good = None
        self.lbl_bad = None
        self.lbl_manutencao = None
        self.lbl_sem_retorno = None

        # gráficos
        self.fig_tipo = None
        self.ax_tipo = None
        self.canvas_tipo = None

        self.fig_modelo = None
        self.ax_modelo = None
        self.canvas_modelo = None

        self.fig_agente = None
        self.ax_agente = None
        self.canvas_agente = None

        self._criar_widgets()
        self._carregar_dados()

        # fade-in suave
        self.after(10, lambda: aplicar_fade_in(self, duracao=300))

    # ------------------------------------------------------------------ #
    # CRIAÇÃO DE WIDGETS
    # ------------------------------------------------------------------ #
    def _criar_widgets(self):
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # =================== FILTROS ===================
        frame_filtros = ctk.CTkFrame(container)
        frame_filtros.pack(fill="x", pady=(0, 10))

        lbl_filtros = ctk.CTkLabel(
            frame_filtros, text="Filtros", font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_filtros.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")

        # Data início
        lbl_inicio = ctk.CTkLabel(frame_filtros, text="Data início (saída):")
        lbl_inicio.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.entry_data_inicio = DateEntry(
            frame_filtros, date_pattern="dd/mm/yyyy", width=12
        )
        self.entry_data_inicio.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Data fim
        lbl_fim = ctk.CTkLabel(frame_filtros, text="Data fim (saída):")
        lbl_fim.grid(row=1, column=2, padx=10, pady=5, sticky="w")

        self.entry_data_fim = DateEntry(
            frame_filtros, date_pattern="dd/mm/yyyy", width=12
        )
        self.entry_data_fim.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Status
        lbl_status = ctk.CTkLabel(frame_filtros, text="Status:")
        lbl_status.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.combo_status = ctk.CTkComboBox(
            frame_filtros,
            values=["TODOS", "GOOD", "BAD", "EM MANUTENÇÃO"],
            width=160
        )
        self.combo_status.set("TODOS")
        self.combo_status.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Agente (valores serão preenchidos após carregar dados)
        lbl_agente = ctk.CTkLabel(frame_filtros, text="Agente:")
        lbl_agente.grid(row=2, column=2, padx=10, pady=5, sticky="w")

        self.combo_agente = ctk.CTkComboBox(
            frame_filtros,
            values=["TODOS"],
            width=160
        )
        self.combo_agente.set("TODOS")
        self.combo_agente.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # Botões filtros
        btn_aplicar = ctk.CTkButton(
            frame_filtros,
            text="Aplicar Filtros",
            width=140,
            command=self.aplicar_filtros
        )
        btn_aplicar.grid(row=1, column=4, padx=10, pady=5)

        btn_limpar = ctk.CTkButton(
            frame_filtros,
            text="Limpar",
            width=100,
            command=self.limpar_filtros
        )
        btn_limpar.grid(row=2, column=4, padx=10, pady=5)

        # ajuste de colunas
        for col in range(5):
            frame_filtros.grid_columnconfigure(col, weight=0)
        frame_filtros.grid_columnconfigure(5, weight=1)

        # =================== CARDS (RESUMO) ===================
        frame_cards = ctk.CTkFrame(container)
        frame_cards.pack(fill="x", pady=(0, 10))

        # Card helper
        def criar_card(parent, titulo: str):
            card = ctk.CTkFrame(parent)
            card.pack(side="left", expand=True, fill="x", padx=5, pady=5)

            lbl_t = ctk.CTkLabel(
                card, text=titulo, font=ctk.CTkFont(size=14, weight="bold")
            )
            lbl_t.pack(pady=(8, 2))

            lbl_v = ctk.CTkLabel(
                card, text="0", font=ctk.CTkFont(size=22, weight="bold")
            )
            lbl_v.pack(pady=(0, 8))

            return lbl_v

        self.lbl_total = criar_card(frame_cards, "Total de Registros")
        self.lbl_good = criar_card(frame_cards, "GOOD")
        self.lbl_bad = criar_card(frame_cards, "BAD")
        self.lbl_manutencao = criar_card(frame_cards, "Em Manutenção")
        self.lbl_sem_retorno = criar_card(frame_cards, "Sem Retorno")

        # =================== GRÁFICOS ===================
        frame_graficos = ctk.CTkFrame(container)
        frame_graficos.pack(fill="both", expand=True, pady=(0, 10))

        frame_graficos.columnconfigure(0, weight=1)
        frame_graficos.columnconfigure(1, weight=1)
        frame_graficos.rowconfigure(0, weight=1)
        frame_graficos.rowconfigure(1, weight=1)

        # --- Por Tipo ---
        frame_tipo = ctk.CTkFrame(frame_graficos)
        frame_tipo.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        lbl_tipo = ctk.CTkLabel(
            frame_tipo, text="Quantidade por Tipo", font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl_tipo.pack(pady=(5, 0))

        self.fig_tipo = Figure(figsize=(4, 3), dpi=100)
        self.ax_tipo = self.fig_tipo.add_subplot(111)
        self.canvas_tipo = FigureCanvasTkAgg(self.fig_tipo, master=frame_tipo)
        self.canvas_tipo.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # --- Por Modelo ---
        frame_modelo = ctk.CTkFrame(frame_graficos)
        frame_modelo.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        lbl_modelo = ctk.CTkLabel(
            frame_modelo, text="Quantidade por Modelo", font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl_modelo.pack(pady=(5, 0))

        self.fig_modelo = Figure(figsize=(4, 3), dpi=100)
        self.ax_modelo = self.fig_modelo.add_subplot(111)
        self.canvas_modelo = FigureCanvasTkAgg(self.fig_modelo, master=frame_modelo)
        self.canvas_modelo.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # --- Por Agente ---
        frame_agente = ctk.CTkFrame(frame_graficos)
        frame_agente.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        lbl_agente_g = ctk.CTkLabel(
            frame_agente, text="Quantidade por Agente", font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl_agente_g.pack(pady=(5, 0))

        self.fig_agente = Figure(figsize=(6, 3), dpi=100)
        self.ax_agente = self.fig_agente.add_subplot(111)
        self.canvas_agente = FigureCanvasTkAgg(self.fig_agente, master=frame_agente)
        self.canvas_agente.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # =================== RODAPÉ ===================
        frame_rodape = ctk.CTkFrame(container)
        frame_rodape.pack(fill="x", pady=(5, 0))

        btn_sair = ctk.CTkButton(
            frame_rodape,
            text="Sair",
            width=120,
            fg_color="#A83232",
            hover_color="#7A2424",
            command=lambda: self.after(1, self.destroy)
        )
        btn_sair.pack(side="right", padx=10, pady=5)

    # ------------------------------------------------------------------ #
    # CARREGAR / FILTRAR DADOS
    # ------------------------------------------------------------------ #
    def _carregar_dados(self):
        """Carrega todos os registros da base e atualiza filtros + gráficos."""
        self.registros = self.service.listar_registros() or []
        # preenche combo de agentes
        agentes = sorted({reg[5] for reg in self.registros if reg[5]})
        valores_agente = ["TODOS"] + agentes if agentes else ["TODOS"]
        self.combo_agente.configure(values=valores_agente)
        self.combo_agente.set("TODOS")

        # limpa datas inicialmente
        self.entry_data_inicio.delete(0, "end")
        self.entry_data_fim.delete(0, "end")

        self.aplicar_filtros()

    def _parse_data(self, texto: str):
        """Converte 'dd/mm/yyyy' em datetime.date ou None."""
        texto = (texto or "").strip()
        if not texto:
            return None
        try:
            return datetime.strptime(texto, "%d/%m/%Y").date()
        except ValueError:
            return None

    def aplicar_filtros(self):
        """Filtra registros conforme os widgets de filtro e atualiza cards/gráficos."""
        data_ini = self._parse_data(self.entry_data_inicio.get())
        data_fim = self._parse_data(self.entry_data_fim.get())
        status_filtro = self.combo_status.get().strip().upper()
        agente_filtro = self.combo_agente.get().strip().upper()

        filtrados = []

        for reg in self.registros:
            # reg: (id, numero_serie, status, tipo, modelo, agente, quantidade, data_saida, data_retorno)
            status = (reg[2] or "").upper()
            agente = (reg[5] or "").upper()
            data_saida_txt = reg[7] or ""
            data_saida = self._parse_data(data_saida_txt)

            # filtro por data
            if data_ini and (not data_saida or data_saida < data_ini):
                continue
            if data_fim and (not data_saida or data_saida > data_fim):
                continue

            # filtro por status
            if status_filtro != "TODOS" and status != status_filtro:
                continue

            # filtro por agente
            if agente_filtro != "TODOS" and agente != agente_filtro:
                continue

            filtrados.append(reg)

        self.registros_filtrados = filtrados
        self._atualizar_cards()
        self._atualizar_graficos()

    def limpar_filtros(self):
        self.entry_data_inicio.delete(0, "end")
        self.entry_data_fim.delete(0, "end")
        self.combo_status.set("TODOS")
        self.combo_agente.set("TODOS")
        self.aplicar_filtros()

    # ------------------------------------------------------------------ #
    # CARDS
    # ------------------------------------------------------------------ #
    def _atualizar_cards(self):
        regs = self.registros_filtrados

        total = len(regs)
        status_counts = Counter((reg[2] or "").upper() for reg in regs)
        sem_retorno = sum(1 for reg in regs if not (reg[8] or "").strip())

        self.lbl_total.configure(text=str(total))
        self.lbl_good.configure(text=str(status_counts.get("GOOD", 0)))
        self.lbl_bad.configure(text=str(status_counts.get("BAD", 0)))
        self.lbl_manutencao.configure(text=str(status_counts.get("EM MANUTENÇÃO", 0)))
        self.lbl_sem_retorno.configure(text=str(sem_retorno))

    # ------------------------------------------------------------------ #
    # GRÁFICOS
    # ------------------------------------------------------------------ #
    def _atualizar_graficos(self):
        regs = self.registros_filtrados

        # ------------- Por Tipo -------------
        self.ax_tipo.clear()
        if regs:
            counter_tipo = Counter((reg[3] or "") for reg in regs)
            labels = list(counter_tipo.keys())
            valores = list(counter_tipo.values())
            x = range(len(labels))
            self.ax_tipo.bar(x, valores)
            self.ax_tipo.set_xticks(x)
            self.ax_tipo.set_xticklabels(labels, rotation=30, ha="right")
            self.ax_tipo.set_ylabel("Qtd.")
        else:
            self.ax_tipo.text(0.5, 0.5, "Sem dados", ha="center", va="center")
        self.fig_tipo.tight_layout()
        self.canvas_tipo.draw()

        # ------------- Por Modelo -------------
        self.ax_modelo.clear()
        if regs:
            counter_modelo = Counter((reg[4] or "") for reg in regs)
            labels = list(counter_modelo.keys())
            valores = list(counter_modelo.values())
            x = range(len(labels))
            self.ax_modelo.bar(x, valores)
            self.ax_modelo.set_xticks(x)
            self.ax_modelo.set_xticklabels(labels, rotation=30, ha="right")
            self.ax_modelo.set_ylabel("Qtd.")
        else:
            self.ax_modelo.text(0.5, 0.5, "Sem dados", ha="center", va="center")
        self.fig_modelo.tight_layout()
        self.canvas_modelo.draw()

        # ------------- Por Agente -------------
        self.ax_agente.clear()
        if regs:
            counter_agente = Counter((reg[5] or "") for reg in regs)
            labels = list(counter_agente.keys())
            valores = list(counter_agente.values())
            x = range(len(labels))
            self.ax_agente.bar(x, valores)
            self.ax_agente.set_xticks(x)
            self.ax_agente.set_xticklabels(labels, rotation=30, ha="right")
            self.ax_agente.set_ylabel("Qtd.")
        else:
            self.ax_agente.text(0.5, 0.5, "Sem dados", ha="center", va="center")
        self.fig_agente.tight_layout()
        self.canvas_agente.draw()

