"""FastAPI backend for Supabase health and CRUD tests."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client, create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DEFAULT_TEST_TABLE = os.getenv("SUPABASE_TEST_TABLE", "imoveis")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY environment variables must be set before running the API."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Jane Corretora API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jane2.yvesx.com.br",
        "http://localhost:3000",
        "http://localhost:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/imoveis")
def list_imoveis() -> Dict[str, Any]:
    """Retorna todos os imóveis cadastrados."""
    try:
        response = supabase.table("imoveis").select("*").execute()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"imoveis": response.data}


@app.post("/imoveis")
def create_imovel(payload: Optional[Dict[str, Any]] = Body(None)) -> Dict[str, Any]:
    """Insere um novo imóvel."""
    if not payload or not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload inválido para criação de imóvel.")

    try:
        response = supabase.table("imoveis").insert(payload).execute()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"created": response.data}


@app.put("/imoveis/{imovel_id}")
def update_imovel(imovel_id: int, payload: Optional[Dict[str, Any]] = Body(None)) -> Dict[str, Any]:
    """Atualiza os dados de um imóvel existente pelo ID."""
    if not payload or not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload inválido para atualização de imóvel.")

    try:
        response = (
            supabase.table("imoveis").update(payload).eq("id", imovel_id).execute()
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not response.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado.")

    return {"updated": response.data}


@app.delete("/imoveis/{imovel_id}")
def delete_imovel(imovel_id: int) -> Dict[str, Any]:
    """Remove um imóvel pelo ID."""
    try:
        response = supabase.table("imoveis").delete().eq("id", imovel_id).execute()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not response.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado.")

    return {"deleted": response.data}


def resolve_table_name(override: Optional[str]) -> str:
    table_name = (override or DEFAULT_TEST_TABLE).strip()
    if not table_name:
        raise HTTPException(status_code=400, detail="A valid table name must be provided.")
    return table_name


@app.get("/health")
def health() -> Dict[str, str]:
    """Simple readiness probe."""
    return {"status": "ok"}


@app.get("/db-test")
def db_test(table: Optional[str] = Query(None, description="Nome da tabela para testar")) -> Dict[str, Any]:
    """Runs a simple SELECT ... LIMIT 1 to validate the database connection."""
    table_name = resolve_table_name(table)
    try:
        response = supabase.table(table_name).select("*").limit(1).execute()
    except Exception as exc:  # pragma: no cover - pass-through for runtime visibility
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"table": table_name, "data": response.data}


@app.post("/db-insert-test")
def db_insert_test(
    payload: Optional[Dict[str, Any]] = Body(None, description="Dados personalizados para inserir"),
    table: Optional[str] = Query(None, description="Nome da tabela para testar"),
) -> Dict[str, Any]:
    """Attempts to insert a simple record to verify write permissions."""
    table_name = resolve_table_name(table)

    data: Dict[str, Any]
    if payload and isinstance(payload, dict) and payload.get("data"):
        if not isinstance(payload["data"], dict):
            raise HTTPException(status_code=400, detail="'data' deve ser um objeto JSON.")
        data = payload["data"]
    else:
        data = {
            "descricao": "Registro de teste via API",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        response = supabase.table(table_name).insert(data).execute()
    except Exception as exc:  # pragma: no cover - pass-through for runtime visibility
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"table": table_name, "inserted": response.data}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
