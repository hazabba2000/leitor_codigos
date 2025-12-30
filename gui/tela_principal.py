# gui/tela_principal.py
from pathlib import Path
import os
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, TclError
from tkcalendar import DateEntry
from PIL import Image
from core.database import inicializar_banco
from core.registro_service import RegistroService
from core.export_service import exportar_treeview_para_excel, exportar_treeview_para_pdf
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from core.config_service import ConfigService
from gui.animacoes import aplicar_fade_in, aplicar_fade_out
from core.audit_service import AuditService
from gui.tela_logs import TelaLogs

BASE_DIR = Path(__file__).resolve().parent.parent


class App(ctk.CTk):
    def __init__(self, usuario_logado=None):
        super().__init__()

        self.usuario_logado = usuario_logado
        if self.usuario_logado:
            self.perfil_usuario = str(self.usuario_logado.get("perfil", "USER")).upper()
        else:
            self.perfil_usuario = "USER"

        # Tema customizado (se arquivo existir)
        #try:
            #theme_path = BASE_DIR / "assets" / "themes" / "equipamentos-theme.json"
            #if theme_path.exists():
                #ctk.set_default_color_theme(str(theme_path))
        #except Exception as e:
            #print("Não foi possível aplicar tema customizado:", e)

        self.title("Registro de Equipamentos - Leitor de Código de Barras")
        self.geometry("1780x768")
        self.minsize(1024, 600)

        # começa transparente para o fade-in
        self.attributes("-alpha", 0.0)

        # Banco / serviços
        inicializar_banco()
        self.service = RegistroService()
        from core.audit_service import AuditService
        self.audit = AuditService()

        from core.config_service import ConfigService
        self.config_service = ConfigService()

        # Estado interno de imagens
        self.logo_img = None
        self.equip_img = None
        self.caminho_equip_atual = None
        # Estado interno de seleção (registro para edição)
        self.registro_selecionado_id = None

        # Estado interno de ícones (para não dar AttributeError)
        self.icon_salvar = None
        self.icon_novo = None
        self.icon_carregar = None
        self.icon_excluir = None
        self.icon_dashboard = None
        self.icon_usuarios = None
        self.icon_tipos = None
        self.icon_tema = None
        self.icon_excel = None
        self.icon_pdf = None
        self.icon_sair = None
        self.icon_logs = None

        # Carrega tipos/modelos antes da UI (você já tinha isso)
        self.tipos_disponiveis = self.service.listar_tipos_equipamento() or [
            "SMART POS", "PINPAD", "GPRS-WIFI", "BLUETOOTH-GPRS"
        ]
        self.modelos_disponiveis = self.service.listar_modelos() or [
            "P2-A11", "D-188", "D230", "MP35P-ST"
        ]
        self.tipo_default = self.tipos_disponiveis[0]
        self.modelo_default = self.modelos_disponiveis[0]
        try:
            from customtkinter import get_appearance_mode
            self.tema_atual = get_appearance_mode().lower()
        except Exception:
            # se der qualquer problema, assume dark
            self.tema_atual = "dark"
        # Carrega ícones ANTES de criar botões
        self._carregar_icones()
        # Criar interface
        self._criar_widgets()
        self._carregar_logo()
        self.atualizar_imagem_equipamento(self.modelo_default)
        self.carregar_todos_registros()
        self.registro_selecionado_id = None

        # Iniciar animação de entrada
        self.after(10, lambda: aplicar_fade_in(self, duracao=350))

                # Tema de cores customizado (arquivo JSON em assets/themes)
        #try:
        #    theme_path = BASE_DIR / "assets" / "themes" / "equipamentos-theme.json"
        #    if theme_path.exists():
        #        ctk.set_default_color_theme(str(theme_path))
        #except Exception as e:
        #    print("Não foi possível aplicar tema customizado:", e)

    # ------------------------------------------------------------------ #
    # WIDGETS / LAYOUT
    # ----------------------------------------------------------------- #
    def _criar_widgets(self):
        """Cria toda a interface principal, delegando para submétodos."""
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self._criar_topo(container)
        self._criar_botoes(container)
        self._criar_lista(container)

    def _criar_topo(self, container):
        """Cria a parte superior: logo, bloco de cadastro e foto do equipamento."""
        # ===== TOPO: LOGO + BLOCO DE CADASTRO + FOTO EQUIPAMENTO =====
        frame_topo = ctk.CTkFrame(container)
        frame_topo.pack(fill="x", pady=10)

        # Três colunas:
        # 0 = logo, 1 = card, 2 = foto
        frame_topo.grid_columnconfigure(0, weight=0, minsize=320)
        frame_topo.grid_columnconfigure(1, weight=1)
        frame_topo.grid_columnconfigure(2, weight=0, minsize=320)
        frame_topo.grid_rowconfigure(0, weight=1)

        # Frame da LOGO (esquerda)
        frame_logo = ctk.CTkFrame(frame_topo)
        frame_logo.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        # Frame do CARD (centro)
        frame_card = ctk.CTkFrame(frame_topo)
        frame_card.grid(row=0, column=1, sticky="n", pady=10, padx=10)
        frame_card.grid_propagate(True)
        self.frame_card = frame_card

        # Frame da FOTO (direita)
        frame_foto = ctk.CTkFrame(frame_topo)
        frame_foto.grid(row=0, column=2, sticky="nsew", padx=(10, 20), pady=10)

        # LOGO centralizada dentro do frame dela
        self.lbl_logo = ctk.CTkLabel(frame_logo, text="")
        self.lbl_logo.pack(expand=True)

        # FOTO do equipamento centralizada dentro do frame dela
        self.lbl_foto_equip = ctk.CTkLabel(frame_foto, text="")
        self.lbl_foto_equip.pack(expand=True)
        self.lbl_foto_equip.bind("<Button-1>", self._abrir_preview_equipamento)
        self.lbl_foto_equip.bind("<Double-Button-1>", self._abrir_preview_equipamento)

        # ===== TÍTULO E SUBTÍTULO DENTRO DO CARD =====
        lbl_titulo = ctk.CTkLabel(
            frame_card,
            text="Registro de Equipamentos",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        lbl_titulo.grid(row=0, column=0, columnspan=3, pady=(15, 5), sticky="w")

        lbl_subtitulo = ctk.CTkLabel(
            frame_card,
            text="Deixe o cursor em 'Número de Série', use o leitor e pressione ENTER.",
            font=ctk.CTkFont(size=14)
        )
        lbl_subtitulo.grid(row=1, column=0, columnspan=3, pady=(0, 5), sticky="w")

        # ===== USUÁRIO LOGADO =====
        nome_display = ""
        if self.usuario_logado:
            nome_display = (
                self.usuario_logado.get("nome")
                or self.usuario_logado.get("username")
                or self.usuario_logado.get("usuario")
                or ""
            )
        perfil_display = self.perfil_usuario

        texto_usuario = "Usuário: "
        if nome_display:
            texto_usuario += nome_display
        else:
            texto_usuario += "Não identificado"
        texto_usuario += f" ({perfil_display})"

        lbl_usuario = ctk.CTkLabel(
            frame_card,
            text=texto_usuario,
            font=ctk.CTkFont(size=12),
        )
        lbl_usuario.grid(row=2, column=0, columnspan=3, pady=(0, 15), sticky="e")

        # ===== FORMULÁRIO =====
        lbl_numero_serie = ctk.CTkLabel(frame_card, text="Número de Série:")
        lbl_numero_serie.grid(row=3, column=0, sticky="e", padx=5, pady=5)

        self.entry_numero_serie = ctk.CTkEntry(frame_card, width=300)
        self.entry_numero_serie.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        lbl_status = ctk.CTkLabel(frame_card, text="Status:")
        lbl_status.grid(row=4, column=0, sticky="e", padx=5, pady=5)

        self.combo_status = ctk.CTkComboBox(
            frame_card,
            values=["DEVOLVIDA", "EM CAMPO"],
            width=300
        )
        self.combo_status.set("EM CAMPO")
        self.combo_status.grid(row=4, column=1, sticky="w", padx=5, pady=5)

        lbl_tipo = ctk.CTkLabel(frame_card, text="Tipo de Equipamento:")
        lbl_tipo.grid(row=5, column=0, sticky="e", padx=5, pady=5)

        self.combo_tipo = ctk.CTkComboBox(
            frame_card,
            values=self.tipos_disponiveis,
            width=300
        )
        self.combo_tipo.set(self.tipo_default)
        self.combo_tipo.grid(row=5, column=1, sticky="w", padx=5, pady=5)

        lbl_modelo = ctk.CTkLabel(frame_card, text="Modelo:")
        lbl_modelo.grid(row=6, column=0, sticky="e", padx=5, pady=5)

        self.combo_modelo = ctk.CTkComboBox(
            frame_card,
            values=self.modelos_disponiveis,
            width=300,
            command=self._on_modelo_alterado
        )
        self.combo_modelo.set(self.modelo_default)
        self.combo_modelo.grid(row=6, column=1, sticky="w", padx=5, pady=5)

        lbl_agente = ctk.CTkLabel(frame_card, text="Agente:")
        lbl_agente.grid(row=7, column=0, sticky="e", padx=5, pady=5)

        self.combo_agente = ctk.CTkComboBox(
            frame_card,
            values=["AROLDO", "HÉLIO", "FERNADO", "LUCAS", ],
            width=300
        )
        self.combo_agente.set("AROLDO")
        self.combo_agente.grid(row=7, column=1, sticky="w", padx=5, pady=5)

        lbl_data_saida = ctk.CTkLabel(frame_card, text="Data de Saída:")
        lbl_data_saida.grid(row=8, column=0, sticky="e", padx=5, pady=5)

        self.date_saida = DateEntry(
            frame_card, date_pattern="dd/mm/yyyy", width=12
        )
        self.date_saida.grid(row=8, column=1, sticky="w", padx=5, pady=5)

        lbl_data_retorno = ctk.CTkLabel(frame_card, text="Data de Retorno:")
        lbl_data_retorno.grid(row=9, column=0, sticky="e", padx=5, pady=5)

        self.date_retorno = DateEntry(
            frame_card, date_pattern="dd/mm/yyyy", width=12
        )
        self.date_retorno.grid(row=9, column=1, sticky="w", padx=5, pady=5)
        self.date_retorno.delete(0, "end")

        lbl_qtd = ctk.CTkLabel(frame_card, text="Quantidade:")
        lbl_qtd.grid(row=10, column=0, sticky="e", padx=5, pady=5)

        self.entry_quantidade = ctk.CTkEntry(frame_card, width=80)
        self.entry_quantidade.insert(0, "1")
        self.entry_quantidade.grid(row=10, column=1, sticky="w", padx=5, pady=5)

        frame_card.columnconfigure(0, weight=0)
        frame_card.columnconfigure(1, weight=1)


    def _texto_botao_tema(self) -> str:
        # Apenas para exibir um texto amigável no botão
        return "Tema: Escuro" if self.tema_atual == "dark" else "Tema: Claro"

    def alternar_tema(self):
        """Alterna entre tema claro e escuro e salva a preferência no banco."""
        if self.tema_atual == "dark":
            novo = "light"
        else:
            novo = "dark"

        # Aplica no CustomTkinter
        ctk.set_appearance_mode("dark" if novo == "dark" else "light")

        # Atualiza estado interno e salva no banco
        self.tema_atual = novo
        try:
            self.config_service.salvar_tema(novo)
        except Exception as e:
            # não quebra a UI se der algum erro de banco
            print("Erro ao salvar tema:", e)

        # Atualiza o texto do botão, se ele já existir
        if hasattr(self, "btn_tema"):
            self.btn_tema.configure(text=self._texto_botao_tema())

    def _criar_botoes(self, container):
        """Cria a barra de botões principal abaixo do formulário."""
        frame_botoes = ctk.CTkFrame(container)
        frame_botoes.pack(fill="x", padx=10, pady=(5, 10))

        btn_salvar = ctk.CTkButton(
            frame_botoes,
            text="Salvar",
            width=140,
            image=self.icon_salvar,
            compound="left",
            command=self.salvar_registro,
        )
        btn_salvar.pack(side="left", padx=5, pady=3)

        btn_novo = ctk.CTkButton(
            frame_botoes,
            text="Novo",
            width=130,
            image=self.icon_novo,
            compound="left",
            command=self.limpar_formulario,
        )
        btn_novo.pack(side="left", padx=5, pady=3)

        btn_carregar = ctk.CTkButton(
            frame_botoes,
            text="Carregar p/ Edição",
            width=170,
            image=self.icon_carregar,
            compound="left",
            command=self.carregar_selecao_para_formulario,
        )
        btn_carregar.pack(side="left", padx=5, pady=3)

        btn_excluir = ctk.CTkButton(
            frame_botoes,
            text="Excluir",
            width=130,
            image=self.icon_excluir,
            compound="left",
            fg_color="#A83232",
            hover_color="#7A2424",
            command=self.excluir_registro_selecionado,
        )
        btn_excluir.pack(side="left", padx=5, pady=3)
        if self.perfil_usuario != "ADMIN":
            btn_excluir.configure(state="disabled")

        # Botão Tipos / Modelos – só para ADMIN
        if self.perfil_usuario == "ADMIN":
            btn_tipos = ctk.CTkButton(
                frame_botoes,
                text="Tipos / Modelos",
                width=170,
                image=self.icon_tipos,
                compound="left",
                command=self.abrir_gerenciar_tipos_modelos,
            )
            btn_tipos.pack(side="left", padx=5, pady=3)

        btn_dashboard = ctk.CTkButton(
            frame_botoes,
            text="Dashboard",
            width=140,
            image=self.icon_dashboard,
            compound="left",
            command=self.abrir_dashboard,
        )
        btn_dashboard.pack(side="left", padx=5, pady=3)

        # BOTÃO USUÁRIOS – só para ADMIN
        if self.perfil_usuario == "ADMIN":
            btn_usuarios = ctk.CTkButton(
                frame_botoes,
                text="Usuários",
                width=140,
                image=self.icon_usuarios,
                compound="left",
                command=self.abrir_gerenciar_usuarios,
            )
            btn_usuarios.pack(side="left", padx=5, pady=3)

        # Botão Logs – se tiver tela de logs criada
        if self.perfil_usuario == "ADMIN" and hasattr(self, "abrir_tela_logs"):
            btn_logs = ctk.CTkButton(
                frame_botoes,
                text="Logs",
                width=120,
                image=self.icon_logs,
                compound="left",
                command=self.abrir_tela_logs,
            )
            btn_logs.pack(side="left", padx=5, pady=3)

        # Botão tema claro/escuro
        self.btn_tema = ctk.CTkButton(
            frame_botoes,
            text=self._texto_botao_tema(),
            width=150,
            image=self.icon_tema,
            compound="left",
            command=self.alternar_tema,
        )
        self.btn_tema.pack(side="left", padx=5, pady=3)

        btn_exportar_excel = ctk.CTkButton(
            frame_botoes,
            text="Excel",
            width=130,
            image=self.icon_excel,
            compound="left",
            command=self.exportar_excel,
        )
        btn_exportar_excel.pack(side="left", padx=5, pady=3)

        btn_exportar_pdf = ctk.CTkButton(
            frame_botoes,
            text="PDF",
            width=130,
            image=self.icon_pdf,
            compound="left",
            command=self.exportar_pdf,
        )
        btn_exportar_pdf.pack(side="left", padx=5, pady=3)

        btn_sair = ctk.CTkButton(
            frame_botoes,
            text="Sair",
            width=130,
            image=self.icon_sair,
            compound="left",
            fg_color="#A83232",
            hover_color="#7A2424",
            command=self.voltar_para_login,
        )
        btn_sair.pack(side="right", padx=5, pady=3)



    def _criar_lista(self, container):
        """
        Monta a área de filtro + Treeview de registros.
        """

        # ============ BARRA DE FILTRO (ACIMA DA LISTA) ============
        filter_bar = ctk.CTkFrame(container, fg_color="transparent")
        filter_bar.pack(fill="x", padx=10, pady=(10, 5))

        self.entry_filtro = ctk.CTkEntry(
            filter_bar,
            placeholder_text="Filtrar por Nº de Série",
            width=250
        )
        self.entry_filtro.pack(side="left", padx=10, pady=5)

        btn_filtrar = ctk.CTkButton(
            filter_bar,
            text="Filtrar",
            width=100,
            command=self.filtrar_registros,
        )
        btn_filtrar.pack(side="left", padx=5, pady=5)

        btn_limpar_filtro = ctk.CTkButton(
            filter_bar,
            text="Limpar Filtro",
            width=120,
            command=self.limpar_filtro,
        )
        btn_limpar_filtro.pack(side="left", padx=5, pady=5)

        # ============ CONTAINER DO TREEVIEW (ABAIXO DO FILTRO) ============
        tree_container = ctk.CTkFrame(container, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        TITULOS_COLUNAS = {
            "ID": "ID",
            "NUMERO_SERIE": "Número de Série",
            "STATUS": "Status",
            "TIPO": "Tipo",
            "MODELO": "Modelo",
            "AGENTE": "Agente",
            "QUANTIDADE": "Qtd",
            "DATA_SAIDA": "Data de Saída",
            "DATA_RETORNO": "Data de Retorno",
        }

        colunas_tree = (
            "ID",
            "NUMERO_SERIE",
            "STATUS",
            "TIPO",
            "MODELO",
            "AGENTE",
            "QUANTIDADE",
            "DATA_SAIDA",
            "DATA_RETORNO",
        )

        self.tree = ttk.Treeview(
            tree_container,
            columns=colunas_tree,
            show="headings",
        )

        self.tree.pack(fill="both", expand=True)

        # Cabeçalhos e largura básica
        for col in colunas_tree:
            titulo = TITULOS_COLUNAS.get(col, col)
            self.tree.heading(col, text=titulo)
            self.tree.column(col, width=120, anchor="center")

        # Ajuste fino
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("NUMERO_SERIE", width=160, anchor="w")
        self.tree.column("QUANTIDADE", width=90, anchor="center")
        self.tree.column("DATA_SAIDA", width=100, anchor="center")
        self.tree.column("DATA_RETORNO", width=100, anchor="center")

        # ============ DESTACAR REGISTROS SEM RETORNO ============
        self.tree.tag_configure(
            "sem_retorno",
            background="#D75413",
            foreground="white"
        )


        # Colocar o Treeview no container
        self.tree.pack(side="left", fill="both", expand=True)

        # Scroll vertical
        scroll = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        # Eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda e: self.carregar_selecao_para_formulario())

    # ------------------------------------------------------------------ #
    # IMAGENS
    # ------------------------------------------------------------------ #
    def _carregar_logo(self):
        """Carrega a logo da empresa no lado esquerdo."""
        caminho_logo1 = BASE_DIR / "assets" / "logo_empresa.png"
        caminho_logo2 = BASE_DIR / "assets" / "logo.png"

        if caminho_logo1.exists():
            caminho_logo = caminho_logo1
        elif caminho_logo2.exists():
            caminho_logo = caminho_logo2
        else:
            self.lbl_logo.configure(
                text="LOGO",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            return

        img = Image.open(caminho_logo)
        w, h = img.size
        alvo_h = 120  # altura desejada
        escala = alvo_h / h
        alvo_w = int(w * escala)

        self.logo_img = ctk.CTkImage(img, size=(alvo_w, alvo_h))
        self.lbl_logo.configure(image=self.logo_img, text="")

    def _on_modelo_alterado(self, novo_modelo: str):
        """Callback chamado quando o modelo é alterado na combobox."""
        self.atualizar_imagem_equipamento(novo_modelo)

    def _carregar_icones(self):
        """Carrega ícones para os botões principais (se existirem)."""
        self.icon_salvar = None
        self.icon_novo = None
        self.icon_carregar = None
        self.icon_excluir = None
        self.icon_dashboard = None
        self.icon_usuarios = None
        self.icon_tipos = None
        self.icon_tema = None
        self.icon_excel = None
        self.icon_pdf = None
        self.icon_sair = None
        self.icon_logs = None

        def carregar(nome_arquivo, size=(20, 20)):
            try:
                caminho = BASE_DIR / "assets" / "icons" / nome_arquivo
                if not caminho.exists():
                    return None
                img = Image.open(caminho)
                return ctk.CTkImage(img, size=size)
            except Exception:
                return None

        self.icon_salvar = carregar("salvar.png")
        self.icon_novo = carregar("novo.png")
        self.icon_carregar = carregar("carregar.png")
        self.icon_excluir = carregar("excluir.png")
        self.icon_dashboard = carregar("dashboard.png")
        self.icon_usuarios = carregar("usuarios.png")
        self.icon_tipos = carregar("tipos_modelos.png")
        self.icon_tema = carregar("tema.png")
        self.icon_excel = carregar("excel.png")
        self.icon_pdf = carregar("pdf.png")
        self.icon_sair = carregar("sair.png")
        self.icon_logs = carregar("logs.png")

    def atualizar_imagem_equipamento(self, modelo: str):
        """Atualiza a foto do equipamento conforme o modelo selecionado."""
        caminho_abs = self.service.obter_caminho_imagem_modelo(modelo)

        if not caminho_abs:
            self.caminho_equip_atual = None
            try:
                self.lbl_foto_equip.configure(
                    image=None,
                    text="Sem imagem",
                    font=ctk.CTkFont(size=12, weight="normal")
                )
            except TclError:
                pass
            return

        caminho = Path(caminho_abs)  # agora já vem ABSOLUTO do service

        if not caminho.exists():
            self.caminho_equip_atual = None
            try:
                self.lbl_foto_equip.configure(
                    image=None,
                    text="Sem imagem",
                    font=ctk.CTkFont(size=12, weight="normal")
                )
            except TclError:
                pass
            return

        self.caminho_equip_atual = caminho

        # cria a imagem proporcional
        img = Image.open(caminho).convert("RGBA")
        w, h = img.size
        alvo_h = 220
        escala = alvo_h / h
        alvo_w = int(w * escala)

        img_ctk = ctk.CTkImage(img, size=(alvo_w, alvo_h))

        # guarda referência para não ser coletada
        self.equip_img = img_ctk

        try:
            self.lbl_foto_equip.configure(image=self.equip_img, text="")
            # também prende a imagem no próprio label (garantia extra)
            self.lbl_foto_equip.image = self.equip_img
        except TclError:
            # se a janela / widget já foi destruído (ex.: fechando app)
            pass


    def _abrir_preview_equipamento(self, event=None):
        """Abre uma janela com preview avançado da foto do equipamento."""
        if not self.caminho_equip_atual:
            return

        # Janela modal escurecida
        top = ctk.CTkToplevel(self)
        top.title(f"Pré-visualização - {self.combo_modelo.get()}")
        top.geometry("900x650")
        top.minsize(600, 450)
        top.resizable(True, True)

        # tenta transformar em modal depois que a janela estiver visível
        def _fazer_grab():
            try:
                top.grab_set()
            except Exception:
                pass

        top.after(50, _fazer_grab)

        # fundo mais escuro (efeito overlay)
        try:
            top.configure(fg_color="black")
        except Exception:
            pass

        # fade-in suave (usando animacoes.py)
        try:
            from .animacoes import aplicar_fade_in
            top.after(10, lambda: aplicar_fade_in(top, duracao=250))
        except Exception:
            pass

        # ===== FRAME CENTRAL =====
        frame_central = ctk.CTkFrame(top, corner_radius=10)
        frame_central.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_titulo = ctk.CTkLabel(
            frame_central,
            text=f"Modelo: {self.combo_modelo.get()}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_titulo.pack(pady=(10, 5))

        # Área da imagem
        frame_img = ctk.CTkFrame(frame_central)
        frame_img.pack(fill="both", expand=True, padx=10, pady=10)

        # Carrega imagem original
        img_orig = Image.open(self.caminho_equip_atual)
        w_orig, h_orig = img_orig.size

        # Tamanho base (altura ~400)
        alvo_h_base = 400
        escala_base = alvo_h_base / h_orig
        base_w = int(w_orig * escala_base)
        base_h = int(h_orig * escala_base)

        # Guarda informações na janela (para zoom)
        top._img_orig = img_orig
        top._base_size = (base_w, base_h)
        top._zoom = 1.0
        top._zoom_min = 0.5
        top._zoom_max = 3.0

        # Label que exibirá a imagem
        top._img_ctk = ctk.CTkImage(img_orig, size=(base_w, base_h))
        lbl_img = ctk.CTkLabel(frame_img, image=top._img_ctk, text="")
        lbl_img.pack(expand=True)

        # ===== CONTROLES =====
        frame_controles = ctk.CTkFrame(frame_central)
        frame_controles.pack(fill="x", pady=(5, 10))

        lbl_zoom = ctk.CTkLabel(
            frame_controles,
            text="Use a rolagem do mouse para aplicar zoom"
        )
        lbl_zoom.pack(side="left", padx=10, pady=5)

        btn_fechar = ctk.CTkButton(
            frame_controles,
            text="Fechar",
            width=120,
            fg_color="#A83232",
            hover_color="#7A2424",
            command=lambda: top.after(1, top.destroy)
        )
        btn_fechar.pack(side="right", padx=10, pady=5)

        # ===== FUNÇÕES DE ZOOM =====
        def aplicar_zoom(novo_zoom: float):
            novo_zoom = max(top._zoom_min, min(top._zoom_max, novo_zoom))
            top._zoom = novo_zoom

            bw, bh = top._base_size
            novo_w = int(bw * top._zoom)
            novo_h = int(bh * top._zoom)

            top._img_ctk = ctk.CTkImage(top._img_orig, size=(novo_w, novo_h))
            lbl_img.configure(image=top._img_ctk)

        def on_mousewheel(event):
            delta = 0
            if hasattr(event, "delta") and event.delta != 0:
                delta = event.delta
            elif hasattr(event, "num"):
                if event.num == 4:  # scroll up
                    delta = 120
                elif event.num == 5:  # scroll down
                    delta = -120

            if delta > 0:
                aplicar_zoom(top._zoom * 1.1)
            elif delta < 0:
                aplicar_zoom(top._zoom / 1.1)

        # Bind da rolagem em diferentes plataformas
        lbl_img.bind("<MouseWheel>", on_mousewheel)        # Windows / Mac
        lbl_img.bind("<Button-4>", on_mousewheel)          # Linux scroll up
        lbl_img.bind("<Button-5>", on_mousewheel)          # Linux scroll down

        # ===== TELA CHEIA COM DUPLO CLIQUE =====
        top._fullscreen = False

        def toggle_fullscreen(event=None):
            top._fullscreen = not top._fullscreen
            try:
                top.attributes("-fullscreen", top._fullscreen)
            except Exception:
                pass

        lbl_img.bind("<Double-Button-1>", toggle_fullscreen)

        def on_escape(event=None):
            if top._fullscreen:
                try:
                    top.attributes("-fullscreen", False)
                except Exception:
                    pass
                top._fullscreen = False
            else:
                top.after(1, top.destroy)

        top.bind("<Escape>", on_escape)

    # ------------------------------------------------------------------ #
    # LÓGICA / FORMULÁRIO
    # ------------------------------------------------------------------ #
    def _on_tree_select(self, event=None):
        """Guarda o ID do registro selecionado na Treeview."""
        selecao = self.tree.selection()
        if not selecao:
            self.registro_selecionado_id = None
            return

        item_id = selecao[0]
        valores = self.tree.item(item_id, "values")
        if not valores:
            self.registro_selecionado_id = None
            return

        self.registro_selecionado_id = int(valores[0])

    def limpar_formulario(self):
        self.registro_selecionado_id = None
        self.entry_numero_serie.delete(0, "end")
        self.combo_status.set("GOOD")
        self.combo_tipo.set(self.tipo_default)
        self.combo_modelo.set(self.modelo_default)
        self.combo_agente.set("AROLDO")
        self.entry_quantidade.delete(0, "end")
        self.entry_quantidade.insert(0, "1")
        self.date_saida.delete(0, "end")
        self.date_retorno.delete(0, "end")
        self.atualizar_imagem_equipamento(self.modelo_default)

    def carregar_selecao_para_formulario(self):
        selecao = self.tree.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione um registro na lista.")
            return

        item_id = selecao[0]
        valores = self.tree.item(item_id, "values")
        self.registro_selecionado_id = int(valores[0])

        self.entry_numero_serie.delete(0, "end")
        self.entry_numero_serie.insert(0, valores[1])

        self.combo_status.set(valores[2])
        self.combo_tipo.set(valores[3])
        self.combo_modelo.set(valores[4])
        self.combo_agente.set(valores[5])

        self.entry_quantidade.delete(0, "end")
        self.entry_quantidade.insert(0, str(valores[6]))

        self.date_saida.delete(0, "end")
        self.date_retorno.delete(0, "end")
        if valores[7]:
            self.date_saida.insert(0, valores[7])
        if valores[8]:
            self.date_retorno.insert(0, valores[8])

        # foto também é atualizada ao carregar
        self.atualizar_imagem_equipamento(valores[4])

    def salvar_registro(self):
        self.registro_selecionado_id = getattr(self, "registro_selecionado_id", None)
        numero_serie = self.entry_numero_serie.get().strip()
        status = self.combo_status.get().strip()
        tipo = self.combo_tipo.get().strip()
        modelo = self.combo_modelo.get().strip()
        agente = self.combo_agente.get().strip()
        data_saida = self.date_saida.get().strip()
        data_retorno = self.date_retorno.get().strip()
        qtd_texto = self.entry_quantidade.get().strip() or "1"
        

        if not numero_serie:
            messagebox.showwarning("Aviso", "O campo Número de Série é obrigatório.")
            return

        try:
            quantidade = int(qtd_texto)
        except ValueError:
            messagebox.showwarning("Aviso", "Quantidade deve ser um número inteiro.")
            return

        try:
            usuario_username = None
            if self.usuario_logado:
                usuario_username = (
                    self.usuario_logado.get("username")
                    or self.usuario_logado.get("usuario")
                    or self.usuario_logado.get("nome")
                )

            detalhes = (
                f"numero_serie={numero_serie}, status={status}, "
                f"tipo={tipo}, modelo={modelo}, agente={agente}, "
                f"data_saida={data_saida}, data_retorno={data_retorno}, "
                f"quantidade={quantidade}"
            )

            if self.registro_selecionado_id is None:
                # INSERT
                novo_id = self.service.inserir_registro(
                    numero_serie, status, tipo, modelo, agente,
                    data_saida, data_retorno, quantidade
                )
                messagebox.showinfo("Sucesso", f"Registro inserido (ID {novo_id}).")

                # LOG DE INSERÇÃO
                self.audit.registrar(
                    tabela="registros",
                    acao="INSERT",
                    registro_id=novo_id,
                    detalhes=detalhes,
                    usuario=usuario_username,
                )

            else:
                # UPDATE
                self.service.atualizar_registro(
                    self.registro_selecionado_id,
                    numero_serie, status, tipo, modelo, agente,
                    data_saida, data_retorno, quantidade
                )
                messagebox.showinfo("Sucesso", "Registro atualizado com sucesso.")

                # LOG DE ATUALIZAÇÃO
                self.audit.registrar(
                    tabela="registros",
                    acao="UPDATE",
                    registro_id=self.registro_selecionado_id,
                    detalhes=detalhes,
                    usuario=usuario_username,
                )

            self.limpar_formulario()
            self.carregar_todos_registros()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar registro:\n{e}")


    def excluir_registro_selecionado(self):
        # Permissão: só ADMIN pode excluir
        if self.perfil_usuario != "ADMIN":
            messagebox.showwarning("Permissão negada", "Você não tem permissão para excluir registros.")
            return

        if self.registro_selecionado_id is None:
            messagebox.showwarning("Aviso", "Selecione um registro para excluir.")
            return

        if not messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir este registro?"):
            return

        try:
            usuario_username = None
            if self.usuario_logado:
                usuario_username = (
                    self.usuario_logado.get("username")
                    or self.usuario_logado.get("usuario")
                    or self.usuario_logado.get("nome")
                )

            registro_id = self.registro_selecionado_id

            self.service.excluir_registro(registro_id)
            self.limpar_formulario()
            self.carregar_todos_registros()
            messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")

            # LOG DE EXCLUSÃO
            self.audit.registrar(
                tabela="registros",
                acao="DELETE",
                registro_id=registro_id,
                detalhes="Registro excluído",
                usuario=usuario_username,
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir registro:\n{e}")

    def _configurar_logout_automatico(self):
        """Configura o monitoramento de inatividade para logout automático."""
        # Bind global de teclas e cliques do mouse
        self.bind_all("<Key>", self._on_user_activity)
        self.bind_all("<Button>", self._on_user_activity)
        self._agendar_logout()

    def _on_user_activity(self, event=None):
        """Chamado a cada interação do usuário para resetar o timer."""
        self._agendar_logout()

    def _agendar_logout(self):
        """Agenda (ou reagenda) o logout automático."""
        # Cancela agendamento anterior, se houver
        if self._logout_after_id is not None:
            try:
                self.after_cancel(self._logout_after_id)
            except Exception:
                pass

        timeout_ms = int(self.logout_timeout_minutos * 60_000)
        self._logout_after_id = self.after(timeout_ms, self._auto_logout)

    def _auto_logout(self):
        """Efetua logout automático por inatividade."""
        # se a janela já foi destruída, não faz nada
        if not self.winfo_exists():
            return

        messagebox.showinfo(
            "Sessão expirada",
            "Você ficou um tempo sem usar o sistema.\n"
            "Por segurança, será necessário fazer login novamente."
        )
        # Reaproveita a mesma lógica de sair
        from gui.tela_login import LoginWindow
        self.destroy()
        login = LoginWindow()
        login.mainloop()


    # --------- CARREGAR / FILTRAR / EXPORTAR ---------
    def carregar_todos_registros(self):
        """Carrega todos os registros do banco na Treeview."""
        try:
            # ajuste o nome do método caso no RegistroService seja diferente
            registros = self.service.listar_registros()
        except AttributeError:
            # fallback se o método tiver outro nome
            registros = self.service.listar_todos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar registros:\n{e}")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for reg in registros:
            # reg = (ID, NUMERO_SERIE, STATUS, TIPO, MODELO, AGENTE, QUANTIDADE, DATA_SAIDA, DATA_RETORNO)
            data_retorno = reg[8]
            tags = ("sem_retorno",) if not data_retorno else ()
            self.tree.insert("", "end", values=reg, tags=tags)

    def filtrar_registros(self):
        """Filtra registros pelo número de série digitado."""
        termo = self.entry_filtro.get().strip()
        if not termo:
            self.carregar_todos_registros()
            return

        try:
            registros = self.service.filtrar_por_numero_serie(termo)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao filtrar:\n{e}")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for reg in registros:
            data_retorno = reg[8]
            tags = ("sem_retorno",) if not data_retorno else ()
            self.tree.insert("", "end", values=reg, tags=tags)

    def limpar_filtro(self):
        """Limpa o filtro e recarrega todos os registros."""
        self.entry_filtro.delete(0, "end")
        self.carregar_todos_registros()

    def exportar_excel(self):
        itens = self.tree.get_children()
        if not itens:
            messagebox.showinfo("Exportar Excel", "Não há registros para exportar.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")],
            title="Salvar como Excel"
        )
        if not file_path:
            return

        try:
            exportar_treeview_para_excel(self.tree, file_path)
            messagebox.showinfo("Exportar Excel", "Exportação concluída com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar para Excel:\n{e}")

    def exportar_pdf(self):
        itens = self.tree.get_children()
        if not itens:
            messagebox.showinfo("Exportar PDF", "Não há registros para exportar.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            title="Salvar como PDF"
        )
        if not file_path:
            return

        try:
            exportar_treeview_para_pdf(
                self.tree,
                file_path,
                titulo="Relatório de Equipamentos"
            )
            messagebox.showinfo("Exportar PDF", "Exportação para PDF concluída com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar para PDF:\n{e}")

    # --------- TIPOS/MODELOS, DASHBOARD, USUÁRIOS ---------
    def atualizar_tipos_modelos(self):
        """Recarrega tipos e modelos do banco e atualiza as combobox."""
        self.tipos_disponiveis = self.service.listar_tipos_equipamento() or [
            "SMART POS", "PINPAD", "GPRS-WIFI", "BLUETOOTH-GPRS"
        ]
        self.modelos_disponiveis = self.service.listar_modelos() or [
            "P2-A11", "D-188", "D230", "MP35P-ST"
        ]

        # atualiza comboboxes
        self.combo_tipo.configure(values=self.tipos_disponiveis)
        self.combo_modelo.configure(values=self.modelos_disponiveis)

        # garante que um valor válido esteja selecionado
        if self.combo_tipo.get() not in self.tipos_disponiveis:
            self.combo_tipo.set(self.tipos_disponiveis[0])
        if self.combo_modelo.get() not in self.modelos_disponiveis:
            self.combo_modelo.set(self.modelos_disponiveis[0])

    def abrir_gerenciar_tipos_modelos(self):
        # segurança extra: só ADMIN
        if self.perfil_usuario != "ADMIN":
            messagebox.showwarning("Permissão negada", "Apenas administradores podem gerenciar tipos e modelos.")
            return

        from gui.tela_tipos_modelos import TelaTiposModelos
        TelaTiposModelos(self)

    def abrir_dashboard(self):
        from gui.tela_dashboard import TelaDashboard
        TelaDashboard(self, service=self.service)

    def abrir_gerenciar_usuarios(self):
        """Abre a tela de gerenciamento de usuários (apenas para ADMIN)."""
        if self.perfil_usuario != "ADMIN":
            messagebox.showwarning(
                "Permissão negada",
                "Apenas administradores podem gerenciar usuários."
            )
            return

        try:
            from gui.tela_usuarios import TelaUsuarios
            TelaUsuarios(self, usuario_logado=self.usuario_logado)
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Erro ao abrir a tela de usuários:\n{e}"
            )
    def abrir_tela_logs(self):
        """Abre a tela de logs de auditoria (apenas ADMIN)."""
        if self.perfil_usuario != "ADMIN":
            messagebox.showwarning(
                "Permissão negada",
                "Apenas administradores podem visualizar os logs."
            )
            return

        try:
            # Se preferir evitar import no topo, poderia importar aqui:
            # from gui.tela_logs import TelaLogs
            TelaLogs(self, usuario_logado=self.usuario_logado)
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Erro ao abrir a tela de logs:\n{e}"
            )

    def voltar_para_login(self):
        """Pergunta se deseja sair, faz fade-out e volta para a tela de login."""
        from gui.tela_login import LoginWindow

        if not messagebox.askyesno("Sair", "Deseja realmente sair e voltar para a tela de login?"):
            return

        def _abrir_login():
            try:
                self.destroy()
            except Exception:
                pass
            login = LoginWindow()
            login.mainloop()

        # animação de saída
        aplicar_fade_out(self, duracao=250, on_complete=_abrir_login)



        
    
    
