"""Validación rápida de integridad sin acceder a la red."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "app.py", "vigia.py", "monitor_core.py", "online_storage.py",
    ".github/workflows/vigia.yml", ".github/workflows/tests.yml",
    "SETUP_NO_TECNICO.md", "MODELO_DATOS.md", "COMPORTAMIENTO_AGENTICO.md",
    "tests/test_v12_final.py", "fixtures/demo_three_live_stories.json",
]
missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
if missing:
    raise SystemExit("Faltan archivos: " + ", ".join(missing))
for workflow in (ROOT / ".github/workflows").glob("*.yml"):
    if workflow.stat().st_size < 100:
        raise SystemExit(f"Workflow vacío o incompleto: {workflow}")
# Busca patrones típicos de credenciales reales, sin leer ZIP ni fixtures de texto.
problems = []
for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in {".git", "__pycache__", "legacy"} for part in path.parts):
        continue
    if path.suffix.lower() not in {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".json", ".example"}:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if re.search(r'"private_key"\s*:\s*"-----BEGIN PRIVATE KEY-----', text):
        problems.append(str(path.relative_to(ROOT)))
if problems:
    raise SystemExit("Posibles secretos reales: " + ", ".join(problems))
print("Repositorio del Monitor Deportivo válido: archivos, workflows y secretos verificados.")
