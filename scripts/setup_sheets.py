"""Crea y formatea las hojas definitivas usando los secrets del entorno."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import online_storage

if __name__ == "__main__":
    if not online_storage.disponible():
        raise SystemExit("Faltan GOOGLE_SERVICE_ACCOUNT_JSON o SHEET_ID")
    online_storage.asegurar_estructura()
    print("Estructura del Monitor Deportivo creada y hojas técnicas ocultas.")
