"""
Probador rápido de credenciales eToro — sin pasar por el MCP.

Uso:
    ETORO_API_KEY=xxx ETORO_USER_KEY=yyy python test_auth.py

Si devuelve 200 → credenciales OK, pasa a configurar Claude Desktop.
Si devuelve 401 → problema con las claves o entorno (Demo/Real).
"""
import os
import uuid
import httpx

API_KEY = os.environ.get("ETORO_API_KEY", "").strip()
USER_KEY = os.environ.get("ETORO_USER_KEY", "").strip()

if not API_KEY or not USER_KEY:
    print("ERROR: define ETORO_API_KEY y ETORO_USER_KEY como variables de entorno")
    raise SystemExit(1)

headers = {
    "x-api-key": API_KEY,
    "x-user-key": USER_KEY,
    "x-request-id": str(uuid.uuid4()),
    "Accept": "application/json",
}

# Endpoint mínimo, read-only: lista de watchlists del usuario autenticado.
url = "https://public-api.etoro.com/api/v1/trading/info/real/pnl"

print(f"GET {url}")
print(f"x-api-key:  {API_KEY[:6]}...{API_KEY[-4:]}  (len={len(API_KEY)})")
print(f"x-user-key: {USER_KEY[:6]}...{USER_KEY[-4:]}  (len={len(USER_KEY)})")
print()

r = httpx.get(url, headers=headers, timeout=30.0)
print(f"Status: {r.status_code}")
print(f"Body:   {r.text[:500]}")
