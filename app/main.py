import os
from contextlib import asynccontextmanager
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

DATABASE_URL = os.environ["DATABASE_URL"]
API_KEY = os.environ.get("API_KEY", "")


def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@asynccontextmanager
async def lifespan(_: FastAPI):
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
    yield


app = FastAPI(title="Items API", version="1.0.0", lifespan=lifespan)


class ItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)


def require_api_key(x_api_key: Annotated[str | None, Header()] = None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


Auth = Annotated[None, Depends(require_api_key)]


@app.get("/health")
def health():
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@app.get("/api/productos")
def list_products(limit: int = Query(default=100, ge=1, le=500)):
    """Public read-only JSON endpoint for viewing the product catalog in a browser."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, description, created_at FROM items ORDER BY id ASC LIMIT %s",
            (limit,),
        ).fetchall()
    return {
        "data": [
            {
                "id": str(row["id"]),
                "nombre": row["name"],
                "descripcion": row["description"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    }


@app.get("/api/productos/{product_id}")
def get_public_product(product_id: int):
    """Return one product in the same JSON envelope as the catalog endpoint."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, description, created_at FROM items WHERE id = %s",
            (product_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "data": {
            "id": str(row["id"]),
            "nombre": row["name"],
            "descripcion": row["description"],
            "created_at": row["created_at"],
        }
    }


@app.post("/items", status_code=201)
def create_item(item: ItemInput, _: Auth):
    with get_conn() as conn:
        return conn.execute(
            "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING *",
            (item.name, item.description),
        ).fetchone()


@app.get("/items")
def list_items(_: Auth, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM items ORDER BY id DESC LIMIT %s OFFSET %s", (limit, offset)
        ).fetchall()


@app.get("/items/{item_id}")
def get_item(item_id: int, _: Auth):
    with get_conn() as conn:
        item = conn.execute("SELECT * FROM items WHERE id = %s", (item_id,)).fetchone()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemInput, _: Auth):
    with get_conn() as conn:
        updated = conn.execute(
            "UPDATE items SET name = %s, description = %s, updated_at = NOW() WHERE id = %s RETURNING *",
            (item.name, item.description, item_id),
        ).fetchone()
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, _: Auth):
    with get_conn() as conn:
        deleted = conn.execute("DELETE FROM items WHERE id = %s RETURNING id", (item_id,)).fetchone()
    if deleted is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Response(status_code=204)
