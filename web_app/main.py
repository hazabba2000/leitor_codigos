# web_app/main.py
from pathlib import Path
import math

from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel   # ⬅️ ADICIONE ESTA LINHA
from core.database import criar_conexao, inicializar_banco

BASE_DIR = Path(__file__).resolve().parent.parent  # pasta do projeto
APP_DIR = BASE_DIR / "web_app"

app = FastAPI()

# arquivos estáticos (CSS, JS, etc.)
app.mount(
    "/static",
    StaticFiles(directory=APP_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


@app.on_event("startup")
def startup():
    """Garante que o banco está criado quando o servidor sobe."""
    inicializar_banco()


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------
def _get_opcoes_formulario():
    """Lê opções para os selects (status, tipo, modelo, agente)."""

    # listas padrão para garantir que sempre haja opções úteis
    status_padrao = ["EM CAMPO", "ESTOQUE", "MANUTENÇÃO", "GOOD", "RUIM"]
    tipos_padrao = ["SMART POS", "GPRS-WIFI", "BLUETOOTH-GPRS"]
    modelos_padrao = ["P2-A11", "D-188", "D230"]
    agentes_padrao = ["AROLDO", "AGENTE 1", "AGENTE 2"]

    con = criar_conexao()
    cur = con.cursor()

    # -------- STATUS --------
    cur.execute("""
        SELECT DISTINCT status
        FROM registros
        WHERE status IS NOT NULL AND TRIM(status) <> ''
        ORDER BY status;
    """)
    status_db = [row[0].strip() for row in cur.fetchall()]

    # -------- TIPOS --------
    cur.execute("SELECT nome FROM tipos_equipamento ORDER BY nome;")
    tipos_db = [row[0] for row in cur.fetchall()]

    # -------- MODELOS --------
    cur.execute("SELECT nome FROM modelos_equipamento ORDER BY nome;")
    modelos_db = [row[0] for row in cur.fetchall()]

    # -------- AGENTES --------
    cur.execute("""
        SELECT DISTINCT agente
        FROM registros
        WHERE agente IS NOT NULL AND TRIM(agente) <> ''
        ORDER BY agente;
    """)
    agentes_db = [row[0].strip() for row in cur.fetchall()]

    con.close()

    # mistura padrões + banco, removendo duplicados
    status_opcoes = sorted(set(status_padrao + status_db))
    tipos = sorted(set(tipos_padrao + tipos_db)) if tipos_db else tipos_padrao
    modelos = sorted(set(modelos_padrao + modelos_db)) if modelos_db else modelos_padrao
    agentes = sorted(set(agentes_padrao + agentes_db)) if agentes_db else agentes_padrao

    return status_opcoes, tipos, modelos, agentes


def _build_where(
    status: str | None,
    agente: str | None,
    tipo: str | None,
    numero_serie: str | None,
):
    """Monta WHERE dinâmico para filtros."""
    where = []
    params: list[str] = []

    if status:
        where.append("status = ?")
        params.append(status)

    if agente:
        where.append("agente = ?")
        params.append(agente)

    if tipo:
        where.append("tipo_equipamento = ?")
        params.append(tipo)

    if numero_serie:
        where.append("numero_serie LIKE ?")
        params.append(f"%{numero_serie}%")

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    return where_sql, params


def _listar_registros(
    status: str | None = None,
    agente: str | None = None,
    tipo: str | None = None,
    numero_serie: str | None = None,
    page: int = 1,
    page_size: int = 10,
):
    """Lê registros do SQLite com filtros e paginação."""
    if page < 1:
        page = 1

    con = criar_conexao()
    cur = con.cursor()

    where_sql, params = _build_where(status, agente, tipo, numero_serie)

    # total de linhas para paginação
    cur.execute(f"SELECT COUNT(*) FROM registros {where_sql};", params)
    total = cur.fetchone()[0] or 0

    total_pages = max(1, math.ceil(total / page_size))
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * page_size

    cur.execute(
        f"""
        SELECT
            id,
            numero_serie,
            status,
            tipo_equipamento,
            modelo,
            agente,
            data_saida,
            data_retorno,
            quantidade
        FROM registros
        {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?;
        """,
        (*params, page_size, offset),
    )
    rows = cur.fetchall()
    con.close()

    # transforma em lista de dicionários p/ usar r.id, r.numero_serie etc no template
    registros = [
        {
            "id": r[0],
            "numero_serie": r[1],
            "status": r[2],
            "tipo_equipamento": r[3],
            "modelo": r[4],
            "agente": r[5],
            "data_saida": r[6],
            "data_retorno": r[7],
            "quantidade": r[8],
        }
        for r in rows
    ]

    return registros, total, total_pages, page

# -------------------------------------------------------------------
# MODELOS P/ API (Pydantic)
# -------------------------------------------------------------------
class RegistroBase(BaseModel):
    numero_serie: str
    status: str
    tipo_equipamento: str
    modelo: str
    agente: str
    data_saida: str | None = ""
    data_retorno: str | None = ""
    quantidade: int = 1


class RegistroCreate(RegistroBase):
    """Modelo para criação via API."""
    pass


class RegistroRead(RegistroBase):
    """Modelo para leitura (retorno da API)."""
    id: int

    class Config:
        orm_mode = True


# -------------------------------------------------------------------
# ROTAS
# -------------------------------------------------------------------


# 🔹 Raiz "/" sempre redireciona para /novo
@app.get("/")
async def raiz():
    return RedirectResponse(url="/novo")


# 🔹 Tela principal (formulário + filtros + tabela)
@app.get("/novo")
async def form_novo_registro(
    request: Request,
    page: int = Query(1, ge=1),
    filtro_status: str | None = None,
    filtro_agente: str | None = None,
    filtro_tipo: str | None = None,
    filtro_numero_serie: str | None = None,
):
    status_opcoes, tipos, modelos, agentes = _get_opcoes_formulario()

    registros, total, total_pages, page_atual = _listar_registros(
        status=filtro_status,
        agente=filtro_agente,
        tipo=filtro_tipo,
        numero_serie=filtro_numero_serie,
        page=page,
        page_size=10,
    )

    return templates.TemplateResponse(
        "novo_registro.html",
        {
            "request": request,
            "registros": registros,
            "status_opcoes": status_opcoes,
            "tipos": tipos,
            "modelos": modelos,
            "agentes": agentes,
            "filtro_status": filtro_status or "",
            "filtro_agente": filtro_agente or "",
            "filtro_tipo": filtro_tipo or "",
            "filtro_numero_serie": filtro_numero_serie or "",
            "page": page_atual,
            "total_pages": total_pages,
            "total": total,
        },
    )


# 🔹 Recebe o POST do formulário e grava no banco (CREATE)
@app.post("/novo")
async def salvar_registro(
    request: Request,
    numero_serie: str = Form(...),
    status: str = Form(...),
    tipo: str = Form(...),
    modelo: str = Form(...),
    agente: str = Form(...),
    data_saida: str = Form(""),
    data_retorno: str = Form(""),
    quantidade: int = Form(1),
):
    con = criar_conexao()
    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO registros
            (numero_serie, status, tipo_equipamento, modelo,
             agente, data_saida, data_retorno, quantidade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            numero_serie.strip(),
            status.strip(),
            tipo.strip(),
            modelo.strip(),
            agente.strip(),
            data_saida.strip(),
            data_retorno.strip(),
            quantidade,
        ),
    )
    con.commit()
    con.close()

    # Depois de salvar, volta para /novo
    return RedirectResponse(url="/novo", status_code=303)


# 🔹 Carrega um registro para edição
@app.get("/registros/{registro_id}/editar")
async def editar_registro_form(request: Request, registro_id: int):
    status_opcoes, tipos, modelos, agentes = _get_opcoes_formulario()

    con = criar_conexao()
    cur = con.cursor()
    cur.execute(
        """
        SELECT
            id, numero_serie, status, tipo_equipamento, modelo,
            agente, data_saida, data_retorno, quantidade
        FROM registros
        WHERE id = ?;
        """,
        (registro_id,),
    )
    row = cur.fetchone()
    con.close()

    if not row:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    registro = {
        "id": row[0],
        "numero_serie": row[1],
        "status": row[2],
        "tipo_equipamento": row[3],
        "modelo": row[4],
        "agente": row[5],
        "data_saida": row[6],
        "data_retorno": row[7],
        "quantidade": row[8],
    }

    # Reaproveita o mesmo template, mas indicando que é edição
    return templates.TemplateResponse(
        "novo_registro.html",
        {
            "request": request,
            "registro_edicao": registro,
            "status_opcoes": status_opcoes,
            "tipos": tipos,
            "modelos": modelos,
            "agentes": agentes,
            # lista vazia só pra não quebrar (você pode carregar se quiser)
            "registros": [],
            "filtro_status": "",
            "filtro_agente": "",
            "filtro_tipo": "",
            "filtro_numero_serie": "",
            "page": 1,
            "total_pages": 1,
            "total": 0,
        },
    )


# 🔹 Salva edição (UPDATE)
@app.post("/registros/{registro_id}/editar")
async def editar_registro_salvar(
    registro_id: int,
    numero_serie: str = Form(...),
    status: str = Form(...),
    tipo: str = Form(...),
    modelo: str = Form(...),
    agente: str = Form(...),
    data_saida: str = Form(""),
    data_retorno: str = Form(""),
    quantidade: int = Form(1),
):
    con = criar_conexao()
    cur = con.cursor()

    cur.execute(
        """
        UPDATE registros
        SET
            numero_serie = ?,
            status = ?,
            tipo_equipamento = ?,
            modelo = ?,
            agente = ?,
            data_saida = ?,
            data_retorno = ?,
            quantidade = ?
        WHERE id = ?;
        """,
        (
            numero_serie.strip(),
            status.strip(),
            tipo.strip(),
            modelo.strip(),
            agente.strip(),
            data_saida.strip(),
            data_retorno.strip(),
            quantidade,
            registro_id,
        ),
    )
    con.commit()
    con.close()

    return RedirectResponse(url="/novo", status_code=303)


# 🔹 Excluir registro (DELETE)
@app.post("/registros/{registro_id}/excluir")
async def excluir_registro(registro_id: int):
    con = criar_conexao()
    cur = con.cursor()
    cur.execute("DELETE FROM registros WHERE id = ?;", (registro_id,))
    con.commit()
    con.close()

    return RedirectResponse(url="/novo", status_code=303)


# 🔹 Página simples de Estatísticas (por enquanto só layout)
@app.get("/stats")
async def pagina_stats(request: Request):
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
        },
    )

# -------------------------------------------------------------------
# API JSON - para uso futuro em app mobile / frontend moderno
# -------------------------------------------------------------------

@app.get("/api/registros", response_model=list[RegistroRead])
async def api_listar_registros(
    status: str | None = Query(default=None),
    agente: str | None = Query(default=None),
    tipo: str | None = Query(default=None),
    numero_serie: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """
    Lista registros em JSON, com filtros e paginação.
    Exemplo:
      GET /api/registros?status=EM%20CAMPO&page=1&page_size=20
    """
    registros, total, total_pages, page_atual = _listar_registros(
        status=status,
        agente=agente,
        tipo=tipo,
        numero_serie=numero_serie,
        page=page,
        page_size=page_size,
    )

    # Podemos incluir info de paginação via headers depois, se precisar.
    return [RegistroRead(**r) for r in registros]


@app.get("/api/registros/{registro_id}", response_model=RegistroRead)
async def api_obter_registro(registro_id: int):
    """
    Retorna um registro específico em JSON.
    """
    con = criar_conexao()
    cur = con.cursor()
    cur.execute(
        """
        SELECT
            id, numero_serie, status, tipo_equipamento, modelo,
            agente, data_saida, data_retorno, quantidade
        FROM registros
        WHERE id = ?;
        """,
        (registro_id,),
    )
    row = cur.fetchone()
    con.close()

    if not row:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    registro = {
        "id": row[0],
        "numero_serie": row[1],
        "status": row[2],
        "tipo_equipamento": row[3],
        "modelo": row[4],
        "agente": row[5],
        "data_saida": row[6],
        "data_retorno": row[7],
        "quantidade": row[8],
    }

    return RegistroRead(**registro)

@app.post("/api/registros", response_model=RegistroRead, status_code=201)
async def api_criar_registro(dados: RegistroCreate):
    """
    Cria um novo registro via JSON.
    """
    con = criar_conexao()
    cur = con.cursor()

    cur.execute(
        """
        INSERT INTO registros
            (numero_serie, status, tipo_equipamento, modelo,
             agente, data_saida, data_retorno, quantidade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            dados.numero_serie.strip(),
            dados.status.strip(),
            dados.tipo_equipamento.strip(),
            dados.modelo.strip(),
            dados.agente.strip(),
            (dados.data_saida or "").strip(),
            (dados.data_retorno or "").strip(),
            dados.quantidade,
        ),
    )
    novo_id = cur.lastrowid
    con.commit()
    con.close()

    return await api_obter_registro(novo_id)


@app.put("/api/registros/{registro_id}", response_model=RegistroRead)
async def api_atualizar_registro(registro_id: int, dados: RegistroCreate):
    """
    Atualiza um registro existente via JSON.
    """
    # Verifica se existe
    try:
        await api_obter_registro(registro_id)
    except HTTPException:
        raise

    con = criar_conexao()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE registros
        SET
            numero_serie = ?,
            status = ?,
            tipo_equipamento = ?,
            modelo = ?,
            agente = ?,
            data_saida = ?,
            data_retorno = ?,
            quantidade = ?
        WHERE id = ?;
        """,
        (
            dados.numero_serie.strip(),
            dados.status.strip(),
            dados.tipo_equipamento.strip(),
            dados.modelo.strip(),
            dados.agente.strip(),
            (dados.data_saida or "").strip(),
            (dados.data_retorno or "").strip(),
            dados.quantidade,
            registro_id,
        ),
    )
    con.commit()
    con.close()

    return await api_obter_registro(registro_id)


@app.delete("/api/registros/{registro_id}", status_code=204)
async def api_excluir_registro(registro_id: int):
    """
    Exclui um registro via JSON.
    """
    con = criar_conexao()
    cur = con.cursor()
    cur.execute("DELETE FROM registros WHERE id = ?;", (registro_id,))
    con.commit()
    con.close()

    return


