# Arquitectura V12

## Componentes

### Recolección y procesamiento

`vigia.py` corre en GitHub Actions. Obtiene fuentes con concurrencia limitada, conserva publisher y canal de descubrimiento, calcula calidad del corte, agrupa historias, compara el estado anterior y produce la mesa editorial.

### Agentes editoriales

El paquete `editorial_agents/` separa responsabilidades:

- `coverage.py`: comparación semántica con Olé.
- `curator.py`: acción y prioridad.
- `briefing.py`: cambios editoriales reales.
- `discovery.py`: rarezas internacionales, separando noticiabilidad y confianza.
- `desk.py`: resumen 4H, acciones y auditoría.
- `ole_today.py`: memoria del día, publicadas y actualizadas.
- `cut_quality.py`: corte completo o degradado.
- `source_health.py`: estado comprensible de fuentes.
- `orchestrator.py`: coordina el ciclo.

### Persistencia

`online_storage.py` usa Google Sheets con lectura cacheada, escrituras por lote, backoff ante cuota y hojas técnicas ocultas. Un corte degradado no reemplaza el último snapshot completo.

### Interfaz

`app.py` es una app de lectura y feedback. No recolecta fuentes al cargar. Permite:

- lectura de dos minutos o completa;
- actualizar estados de acciones;
- incorporar enlaces sociales;
- consultar auditoría;
- generar el parte ampliado bajo demanda.

## Flujo

```text
Fuentes -> GitHub Actions -> normalización -> historias vivas
        -> comparación -> acción explicada -> Google Sheets
        -> Streamlit -> decisión del editor -> memoria siguiente
```

## Aislamiento

La planilla nueva usa nombres definitivos sin prefijo. La automatización queda apagada mientras se valida. No se escribe en `Agenda` ni `Snapshot` porque las variables `LEGACY_*` están en `false`.
