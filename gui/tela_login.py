# gui/tela_login.py
import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from PIL import Image
from core.database import inicializar_banco
from core.auth_service import AuthService
from gui.animacoes import aplicar_fade_in, centralizar_janela  # usa animacoes.py que está em gui/

BASE_DIR = Path(__file__).resolve().parent.parent


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Login - Registro de Equipamentos")
        self.geometry("400x650")
        self.resizable(False, False)

        # Começa transparente para o fade-in
        self.attributes("-alpha", 0.0)

        inicializar_banco()
        self.auth = AuthService()

        # referência da imagem da logo (para não ser coletada)
        self.logo_img_login = None

        self._criar_widgets()

        # Centralizar e aplicar fade-in
        self.after(10, lambda: centralizar_janela(self))
        self.after(20, lambda: aplicar_fade_in(self, duracao=300))

    # ------------------- UI ------------------- #
    def _criar_widgets(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ========== LOGO NO TOPO ==========
        caminho_logo1 = BASE_DIR / "assets" / "logo_empresa.png"
        caminho_logo2 = BASE_DIR / "assets" / "logo.png"

        caminho_logo = None
        if caminho_logo1.exists():
            caminho_logo = caminho_logo1
        elif caminho_logo2.exists():
            caminho_logo = caminho_logo2

        if caminho_logo:
            img = Image.open(caminho_logo)
            w, h = img.size
            alvo_h = 90  # altura desejada da logo no login
            escala = alvo_h / h
            alvo_w = int(w * escala)

            self.logo_img_login = ctk.CTkImage(img, size=(alvo_w, alvo_h))
            lbl_logo = ctk.CTkLabel(frame, image=self.logo_img_login, text="")
            lbl_logo.pack(pady=(5, 5))
        else:
            # se não achar imagem, mostra só o texto "LOGO"
            lbl_logo = ctk.CTkLabel(
                frame,
                text="LOGO",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            lbl_logo.pack(pady=(5, 5))

        # ========== TÍTULO E SUBTÍTULO ==========
        lbl_titulo = ctk.CTkLabel(
            frame,
            text="Registro de Equipamentos",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        lbl_titulo.pack(pady=(5, 2))

        lbl_sub = ctk.CTkLabel(
            frame,
            text="Faça login para continuar",
            font=ctk.CTkFont(size=12)
        )
        lbl_sub.pack(pady=(0, 15))

        # Campo usuário
        lbl_user = ctk.CTkLabel(frame, text="Usuário:")
        lbl_user.pack(anchor="w")
        self.entry_user = ctk.CTkEntry(frame, width=260)
        self.entry_user.pack(pady=(0, 10))

        # Campo senha
        lbl_senha = ctk.CTkLabel(frame, text="Senha:")
        lbl_senha.pack(anchor="w")
        self.entry_senha = ctk.CTkEntry(frame, width=260, show="*")
        self.entry_senha.pack(pady=(0, 10))

        # Tema: Sistema / Claro / Escuro
        lbl_tema = ctk.CTkLabel(frame, text="Tema:")
        lbl_tema.pack(anchor="w", pady=(8, 0))

        self.segmento_tema = ctk.CTkSegmentedButton(
            frame,
            values=["Sistema", "Claro", "Escuro"],
            command=self._alterar_tema
        )
        self.segmento_tema.set("Sistema")
        self.segmento_tema.pack(pady=(2, 10))

        # Botão ENTRAR
        btn_entrar = ctk.CTkButton(
            frame,
            text="Entrar",
            width=200,
            command=self._tentar_login
        )
        btn_entrar.pack(pady=(10, 5))

        # ENTER = login
        self.bind("<Return>", lambda e: self._tentar_login())

        # Botão FECHAR
        btn_fechar = ctk.CTkButton(
            frame,
            text="Fechar",
            width=200,
            fg_color="#A83232",
            hover_color="#7A2424",
            command=self._fechar_aplicacao
        )
        btn_fechar.pack(pady=(0, 10))


    # ------------------- LÓGICA ------------------- #
    def _alterar_tema(self, valor: str):
        v = valor.lower()
        if v == "sistema":
            ctk.set_appearance_mode("system")
        elif v == "claro":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

    def _tentar_login(self):
        username = self.entry_user.get().strip()
        senha = self.entry_senha.get().strip()

        if not username or not senha:
            messagebox.showwarning("Aviso", "Informe usuário e senha.")
            return

        usuario = self.auth.autenticar(username, senha)
        if not usuario:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.")
            return

        # Login OK -> abrir tela principal
        self._abrir_app_principal(usuario)

    def _abrir_app_principal(self, usuario):
        from gui.tela_principal import App  # import tardio para evitar loop

        # fecha janela de login
        self.destroy()

        # abre app principal, passando usuário logado
        app = App(usuario_logado=usuario)
        app.mainloop()
    
    def _fechar_aplicacao(self):
        """Fecha completamente o sistema."""
        self.destroy()

