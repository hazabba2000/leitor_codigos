import customtkinter as ctk


def aplicar_fade_in(janela, duracao: int = 300):
    try:
        janela.update_idletasks()
    except Exception:
        pass

    steps = 20
    delay = max(10, int(duracao / steps))

    def _fade(step=0):
        alpha = step / steps
        try:
            janela.attributes("-alpha", alpha)
        except Exception:
            return

        if step < steps:
            janela.after(delay, _fade, step + 1)

    _fade(0)


def centralizar_janela(janela):
    try:
        janela.update_idletasks()
    except Exception:
        pass

    # tenta usar tk::PlaceWindow (melhor em múltiplos monitores)
    try:
        janela.eval(f"tk::PlaceWindow {str(janela)} center")
        return
    except Exception:
        pass

    # fallback manual
    try:
        janela.update_idletasks()
        largura = janela.winfo_width()
        altura = janela.winfo_height()
        sw = janela.winfo_screenwidth()
        sh = janela.winfo_screenheight()
        x = int((sw - largura) / 2)
        y = int((sh - altura) / 2)
        janela.geometry(f"+{x}+{y}")
    except Exception:
        pass

def aplicar_fade_out(janela, duracao=300, on_complete=None):
    """
    Faz a janela desaparecer suavemente.
    Se on_complete for passado, chama a função ao final.
    Caso contrário, dá destroy() na janela.
    """
    try:
        alpha_atual = float(janela.attributes("-alpha"))
    except Exception:
        alpha_atual = 1.0

    passos = 15
    delay = max(10, int(duracao / passos))

    def _step(alpha):
        if alpha <= 0:
            if on_complete:
                on_complete()
            else:
                try:
                    janela.destroy()
                except Exception:
                    pass
            return

        try:
            janela.attributes("-alpha", alpha)
        except Exception:
            # se a janela já foi destruída, apenas para
            if on_complete:
                on_complete()
            return

        janela.after(delay, lambda: _step(alpha - (alpha_atual / passos)))

    _step(alpha_atual)
