# core/export_service.py
"""
Serviço para exportação de dados da Treeview para Excel e PDF.

Isola a lógica pesada de exportação, deixando as telas (GUI) mais limpas.
"""

from typing import Sequence
from tkinter import ttk

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def exportar_treeview_para_excel(tree: ttk.Treeview, file_path: str) -> None:
    """
    Exporta os dados de uma Treeview para arquivo Excel (.xlsx).

    :param tree: widget ttk.Treeview com colunas e linhas preenchidas.
    :param file_path: caminho completo do arquivo .xlsx a ser salvo.
    """
    itens = tree.get_children()
    if not itens:
        # Se não tiver linhas, simplesmente cria uma planilha com cabeçalhos
        wb = Workbook()
        ws = wb.active
        ws.title = "Registros"

        colunas = tree["columns"]
        headers = [tree.heading(col, "text") or col for col in colunas]
        ws.append(headers)

        wb.save(file_path)
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Registros"

    # Cabeçalhos
    colunas = tree["columns"]
    headers = [tree.heading(col, "text") or col for col in colunas]
    ws.append(headers)

    # Linhas
    for item in itens:
        valores = tree.item(item, "values")
        ws.append(list(valores))

    wb.save(file_path)


def exportar_treeview_para_pdf(
    tree: ttk.Treeview,
    file_path: str,
    titulo: str = "Relatório de Registros"
) -> None:
    """
    Exporta os dados de uma Treeview para um PDF simples em formato tabela.
    :param tree: widget ttk.Treeview.
    :param file_path: caminho do PDF.
    :param titulo: texto do título no topo do PDF.
    """
    itens = tree.get_children()
    c = canvas.Canvas(file_path, pagesize=A4)
    largura, altura = A4

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, altura - 50, titulo)

    # Cabeçalhos
    colunas = tree["columns"]
    headers = [tree.heading(col, "text") or col for col in colunas]

    y = altura - 80
    c.setFont("Helvetica-Bold", 9)

    # Larguras básicas das colunas – se quiser, dá pra refinar depois
    # Aqui usamos uma largura fixa proporcional.
    if colunas:
        col_width = (largura - 80) / len(colunas)
    else:
        col_width = 60

    x = 40
    for header in headers:
        c.drawString(x, y, str(header)[:18])
        x += col_width

    # Linhas
    c.setFont("Helvetica", 9)
    y -= 15

    for item in itens:
        if y < 50:
            c.showPage()
            c.setFont("Helvetica-Bold", 9)
            y = altura - 50

            # redesenha cabeçalhos em nova página
            x = 40
            for header in headers:
                c.drawString(x, y, str(header)[:18])
                x += col_width
            c.setFont("Helvetica", 9)
            y -= 15

        valores = list(tree.item(item, "values"))
        x = 40
        for valor in valores:
            texto = str(valor)
            c.drawString(x, y, texto[:18])
            x += col_width
        y -= 15

    c.showPage()
    c.save()
