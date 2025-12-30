# gui/tela_tipos_modelos.py
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import sys
from PIL import Image
from core.equipamento_service import EquipamentoService
from gui.animacoes import aplicar_fade_in, centralizar_janela

BASE_DIR = Path(__file__).resolve().parent.parent


class TelaTiposModelos(ctk.CTkToplevel):
    def __init__(self, master=None, callback_atualizar=None):
        super().__init__(master)

        sys.path.append(str(Path(__file__).resolve().parent.parent))
        self.title("Gerenciar Tipos e Modelos")
        self.geometry("1100x500")
        self.after(10, lambda: centralizar_janela(self))
        self.after(20, lambda: aplicar_fade_in(self, duracao=300))

        self.resizable(True, True)

        self.service = EquipamentoService()
        self.callback_atualizar = callback_atualizar

        # estado interno
        self.tipo_id_selecionado = None
        self.modelo_id_selecionado = None
        self.path_imagem_modelo = None
        self.preview_img = None

        self._criar_widgets()
        self._carregar_tipos()
        self._carregar_modelos()

        # centralizar na tela
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = int((sw - w) / 2)
        y = int((sh - h) / 3)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.after(10, lambda: aplicar_fade_in(self, duracao=300))

    # ----------------- UI ----------------- #
    def _criar_widgets(self):
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT: TIPOS
        frame_tipos = ctk.CTkFrame(container)
        frame_tipos.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)

        lbl_tipos = ctk.CTkLabel(
            frame_tipos,
            text="Tipos de Equipamento",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_tipos.pack(pady=(5, 5))

        frame_form_tipo = ctk.CTkFrame(frame_tipos)
        frame_form_tipo.pack(fill="x", padx=5, pady=5)

        lbl_nome_tipo = ctk.CTkLabel(frame_form_tipo, text="Nome do Tipo:")
        lbl_nome_tipo.grid(row=0, column=0, sticky="e", padx=5, pady=5)

        self.entry_nome_tipo = ctk.CTkEntry(frame_form_tipo, width=200)
        self.entry_nome_tipo.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        frame_botoes_tipo = ctk.CTkFrame(frame_form_tipo)
        frame_botoes_tipo.grid(row=1, column=0, columnspan=2, pady=5)

        btn_add_tipo = ctk.CTkButton(
            frame_botoes_tipo, text="Adicionar Tipo", width=120,
            command=self._salvar_tipo
        )
        btn_add_tipo.pack(side="left", padx=5)

        btn_limpar_tipo = ctk.CTkButton(
            frame_botoes_tipo, text="Limpar", width=80,
            command=self._limpar_tipo
        )
        btn_limpar_tipo.pack(side="left", padx=5)

        btn_excluir_tipo = ctk.CTkButton(
            frame_botoes_tipo, text="Excluir", width=80,
            fg_color="#A83232", hover_color="#7A2424",
            command=self._excluir_tipo
        )
        btn_excluir_tipo.pack(side="left", padx=5)

        frame_tree_tipo = ctk.CTkFrame(frame_tipos)
        frame_tree_tipo.pack(fill="both", expand=True, padx=5, pady=(5, 5))

        self.tree_tipos = ttk.Treeview(
            frame_tree_tipo,
            columns=("id", "nome"),
            show="headings",
            height=8
        )
        self.tree_tipos.heading("id", text="ID")
        self.tree_tipos.heading("nome", text="Nome do Tipo")
        self.tree_tipos.column("id", width=40, anchor="center")
        self.tree_tipos.column("nome", width=200, anchor="w")
        self.tree_tipos.pack(fill="both", expand=True)

        self.tree_tipos.bind("<<TreeviewSelect>>", self._on_select_tipo)

        # RIGHT: MODELOS
        frame_modelos = ctk.CTkFrame(container)
        frame_modelos.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)

        lbl_modelos = ctk.CTkLabel(
            frame_modelos,
            text="Modelos de Equipamento",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_modelos.pack(pady=(5, 5))

        frame_form_modelo = ctk.CTkFrame(frame_modelos)
        frame_form_modelo.pack(fill="x", padx=5, pady=5)

        lbl_nome_modelo = ctk.CTkLabel(frame_form_modelo, text="Nome do Modelo:")
        lbl_nome_modelo.grid(row=0, column=0, sticky="e", padx=5, pady=5)

        self.entry_nome_modelo = ctk.CTkEntry(frame_form_modelo, width=200)
        self.entry_nome_modelo.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        lbl_tipo_modelo = ctk.CTkLabel(frame_form_modelo, text="Tipo vinculado:")
        lbl_tipo_modelo.grid(row=1, column=0, sticky="e", padx=5, pady=5)

        self.combo_tipo_modelo = ctk.CTkComboBox(frame_form_modelo, width=200, values=[])
        self.combo_tipo_modelo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Seleção de imagem
        lbl_img = ctk.CTkLabel(frame_form_modelo, text="Imagem:")
        lbl_img.grid(row=2, column=0, sticky="e", padx=5, pady=5)

        frame_img = ctk.CTkFrame(frame_form_modelo)
        frame_img.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        self.lbl_path_img = ctk.CTkLabel(frame_img, text="Nenhuma imagem")
        self.lbl_path_img.pack(anchor="w")

        btn_escolher_img = ctk.CTkButton(
            frame_img,
            text="Selecionar Imagem",
            width=140,
            command=self._selecionar_imagem_modelo
        )
        btn_escolher_img.pack(anchor="w", pady=(5, 5))
        
                # ===== RODAPÉ COM BOTÃO SAIR =====
        frame_rodape = ctk.CTkFrame(container)
        frame_rodape.pack(fill="x", pady=(5, 0))

        btn_sair = ctk.CTkButton(
            frame_rodape,
            text="Sair",
            width=120,
            fg_color="#A83232",
            hover_color="#7A2424",
            command=self.destroy
        )
        btn_sair.pack(side="right", padx=10, pady=5)

        # Preview pequeno
        self.lbl_preview = ctk.CTkLabel(frame_form_modelo, text="")
        self.lbl_preview.grid(row=0, column=2, rowspan=3, padx=10, pady=5)

        frame_botoes_modelo = ctk.CTkFrame(frame_form_modelo)
        frame_botoes_modelo.grid(row=3, column=0, columnspan=3, pady=5)

        btn_add_modelo = ctk.CTkButton(
            frame_botoes_modelo, text="Salvar Modelo", width=120,
            command=self._salvar_modelo
        )
        btn_add_modelo.pack(side="left", padx=5)

        btn_limpar_modelo = ctk.CTkButton(
            frame_botoes_modelo, text="Limpar", width=80,
            command=self._limpar_modelo
        )
        btn_limpar_modelo.pack(side="left", padx=5)

        btn_excluir_modelo = ctk.CTkButton(
            frame_botoes_modelo, text="Excluir", width=80,
            fg_color="#A83232", hover_color="#7A2424",
            command=self._excluir_modelo
        )
        btn_excluir_modelo.pack(side="left", padx=5)

        frame_tree_modelo = ctk.CTkFrame(frame_modelos)
        frame_tree_modelo.pack(fill="both", expand=True, padx=5, pady=(5, 5))

        self.tree_modelos = ttk.Treeview(
            frame_tree_modelo,
            columns=("id", "nome", "tipo", "imagem"),
            show="headings",
            height=8
        )
        self.tree_modelos.heading("id", text="ID")
        self.tree_modelos.heading("nome", text="Modelo")
        self.tree_modelos.heading("tipo", text="Tipo")
        self.tree_modelos.heading("imagem", text="Imagem")
        self.tree_modelos.column("id", width=40, anchor="center")
        self.tree_modelos.column("nome", width=140, anchor="w")
        self.tree_modelos.column("tipo", width=120, anchor="w")
        self.tree_modelos.column("imagem", width=200, anchor="w")
        self.tree_modelos.pack(fill="both", expand=True)

        self.tree_modelos.bind("<<TreeviewSelect>>", self._on_select_modelo)

    # ----------------- CARREGAR / REFRESH ----------------- #
    def _carregar_tipos(self):
        for item in self.tree_tipos.get_children():
            self.tree_tipos.delete(item)

        tipos = self.service.listar_tipos()
        for tid, nome in tipos:
            self.tree_tipos.insert("", "end", values=(tid, nome))

        # atualizar combo de tipos nos modelos
        nomes_tipos = [t[1] for t in tipos]
        self.combo_tipo_modelo.configure(values=nomes_tipos)

    def _carregar_modelos(self):
        for item in self.tree_modelos.get_children():
            self.tree_modelos.delete(item)

        modelos = self.service.listar_modelos()
        for mid, nome, tipo_nome, img in modelos:
            self.tree_modelos.insert(
                "", "end",
                values=(mid, nome, tipo_nome or "", img or "")
            )

    # ----------------- TIPOS - AÇÕES ----------------- #
    def _limpar_tipo(self):
        self.tipo_id_selecionado = None
        self.entry_nome_tipo.delete(0, "end")

    def _salvar_tipo(self):
        nome = self.entry_nome_tipo.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome do tipo.")
            return

        try:
            if self.tipo_id_selecionado is None:
                self.service.inserir_tipo(nome)
            else:
                self.service.atualizar_tipo(self.tipo_id_selecionado, nome)

            self._limpar_tipo()
            self._carregar_tipos()
            self._carregar_modelos()  # caso mude nomes usados em modelos
            self._notificar_callback()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar tipo:\n{e}")

    def _excluir_tipo(self):
        if self.tipo_id_selecionado is None:
            messagebox.showwarning("Aviso", "Selecione um tipo para excluir.")
            return

        if not messagebox.askyesno("Confirmar", "Excluir este tipo?"):
            return

        try:
            self.service.excluir_tipo(self.tipo_id_selecionado)
            self._limpar_tipo()
            self._carregar_tipos()
            self._carregar_modelos()
            self._notificar_callback()
        except ValueError as ve:
            messagebox.showwarning("Aviso", str(ve))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir tipo:\n{e}")

    def _on_select_tipo(self, event=None):
        selecao = self.tree_tipos.selection()
        if not selecao:
            return
        item_id = selecao[0]
        tid, nome = self.tree_tipos.item(item_id, "values")
        self.tipo_id_selecionado = int(tid)
        self.entry_nome_tipo.delete(0, "end")
        self.entry_nome_tipo.insert(0, nome)

    # ----------------- MODELOS - AÇÕES ----------------- #
    def _limpar_modelo(self):
        self.modelo_id_selecionado = None
        self.entry_nome_modelo.delete(0, "end")
        self.combo_tipo_modelo.set("")
        self.path_imagem_modelo = None
        self.lbl_path_img.configure(text="Nenhuma imagem")
        self.lbl_preview.configure(image=None, text="")

    def _selecionar_imagem_modelo(self):
        file_path = filedialog.askopenfilename(
            title="Selecione uma imagem",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp *.PNG *.JPG *.JPEG *.GIF *.BMP"),
                ("Todos os arquivos", "*.*"),
            ],
            initialdir=str(BASE_DIR / "assets" / "equipamentos")
        )
        if not file_path:
            return

        self.path_imagem_modelo = file_path
        self.lbl_path_img.configure(text=str(Path(file_path).name))

        # preview pequeno
        img = Image.open(file_path)
        w, h = img.size
        alvo_h = 80
        escala = alvo_h / h
        alvo_w = int(w * escala)

        self.preview_img = ctk.CTkImage(img, size=(alvo_w, alvo_h))
        self.lbl_preview.configure(image=self.preview_img, text="")

    def _salvar_modelo(self):
        nome = self.entry_nome_modelo.get().strip()
        tipo_nome = self.combo_tipo_modelo.get().strip() or None
        caminho_imagem = None

        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome do modelo.")
            return

        if self.path_imagem_modelo:
            # salvar caminho relativo ao projeto se estiver dentro dele
            p = Path(self.path_imagem_modelo)
            try:
                caminho_imagem = str(p.relative_to(BASE_DIR))
            except ValueError:
                # fora do projeto -> salva caminho absoluto mesmo
                caminho_imagem = str(p)

        try:
            if self.modelo_id_selecionado is None:
                self.service.inserir_modelo(nome, tipo_nome, caminho_imagem)
            else:
                self.service.atualizar_modelo(
                    self.modelo_id_selecionado,
                    nome,
                    tipo_nome,
                    caminho_imagem
                )

            self._limpar_modelo()
            self._carregar_modelos()
            self._notificar_callback()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar modelo:\n{e}")

    def _excluir_modelo(self):
        if self.modelo_id_selecionado is None:
            messagebox.showwarning("Aviso", "Selecione um modelo para excluir.")
            return

        if not messagebox.askyesno("Confirmar", "Excluir este modelo?"):
            return

        try:
            self.service.excluir_modelo(self.modelo_id_selecionado)
            self._limpar_modelo()
            self._carregar_modelos()
            self._notificar_callback()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir modelo:\n{e}")

    def _on_select_modelo(self, event=None):
        selecao = self.tree_modelos.selection()
        if not selecao:
            return
        item_id = selecao[0]
        mid, nome, tipo_nome, caminho_imagem = self.tree_modelos.item(item_id, "values")
        self.modelo_id_selecionado = int(mid)
        self.entry_nome_modelo.delete(0, "end")
        self.entry_nome_modelo.insert(0, nome)
        self.combo_tipo_modelo.set(tipo_nome or "")
        self.path_imagem_modelo = caminho_imagem or None
        self.lbl_path_img.configure(
            text=Path(caminho_imagem).name if caminho_imagem else "Nenhuma imagem"
        )

        # preview se houver imagem
        if caminho_imagem:
            caminho = Path(caminho_imagem)
            if not caminho.is_absolute():
                caminho = BASE_DIR / caminho
            if caminho.exists():
                img = Image.open(caminho)
                w, h = img.size
                alvo_h = 80
                escala = alvo_h / h
                alvo_w = int(w * escala)
                self.preview_img = ctk.CTkImage(img, size=(alvo_w, alvo_h))
                self.lbl_preview.configure(image=self.preview_img, text="")
            else:
                self.lbl_preview.configure(image=None, text="")

    def _notificar_callback(self):
        """Notifica a tela principal para recarregar os combos, se fornecido."""
        if self.callback_atualizar:
            try:
                self.callback_atualizar()
            except Exception:
                pass
