# API PostgreSQL + n8n

API CRUD de ejemplo construida con FastAPI y PostgreSQL. Al iniciar por primera vez, la API agrega los 15 productos de ejemplo a una base vacía, incluida la base nueva de Render.

## Endpoints
- `GET /health`: estado de API y base.
- `POST /items`: crear registro JSON con `name` y `description` opcional.
- `GET /items?limit=100&offset=0`: listar registros.
- `GET /items/{id}`: consultar un registro.
- `PUT /items/{id}`: reemplazar nombre y descripción.
- `DELETE /items/{id}`: eliminar registro.

El catálogo público se puede ver en `GET /api/productos`, que devuelve los registros bajo `data` como JSON. Para consultar un registro por ID, usa `GET /api/productos/1`. Las rutas CRUD de `/items` requieren el header `X-API-Key`.

## Despliegue en Render
1. En Render, usa **New → Blueprint** y conecta el repositorio.
2. Render leerá `render.yaml`, creará una base PostgreSQL y el servicio `api-productos-adilene`; al iniciar, se cargará el catálogo de ejemplo si la base está vacía.
3. Cuando termine el deploy, confirma su URL en Render; será parecida a `https://api-productos-adilene.onrender.com`. Revisa `/health`, `/docs` y `/api/productos`.
4. Copia el valor de `API_KEY` del Environment del servicio. No lo publiques en el workflow.

## n8n
Crea una credencial **Header Auth** con nombre de header `X-API-Key` y valor de `API_KEY`. En un nodo **HTTP Request**, usa la URL pública del servicio y rutas como `/items`.

Ejemplo para crear un item:
- Method: `POST`
- URL: `https://<servicio>.onrender.com/items`
- Body Content Type: JSON
- Body: `{"name":"Pedido 123","description":"Alta desde n8n"}`

Para consultar, usa `GET https://<servicio>.onrender.com/items` con la misma credencial.

## Docker local
Desde la raíz del repositorio ejecuta `docker compose up --build -d`; servicio local: `http://localhost:8000`.
