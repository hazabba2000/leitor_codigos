# main.py
import customtkinter as ctk
from core.config_service import ConfigService
from gui.tela_login import LoginWindow  # ajuste se o nome for diferente
from core.bootstrap_admin import bootstrap_default_admin

bootstrap_default_admin()


def main():
    # Carrega / detecta tema preferido
    config = ConfigService()
    tema = config.obter_tema_preferido()  # 'dark' ou 'light'

    # Aplica tema global do CustomTkinter
    if tema == "dark":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

    # (opcional) tema de cores padrão
    #ctk.set_default_color_theme("blue")  # você pode trocar por 'dark-blue', etc.

    # Abre a tela de login
    app = LoginWindow()
    app.mainloop()


if __name__ == "__main__":
    main()

