# Monitor Deportivo · proyecto nuevo

Este directorio es una reconstrucción aislada del monitor de noticias. No modifica el monitor antiguo, sus hojas ni sus workflows.

## Fase actual

La primera fase contiene el núcleo editorial sin red ni credenciales:

- modelo de fuentes, artículos, historias y cortes;
- fechas verificables en `America/Argentina/Buenos_Aires`;
- clasificación confirmada/probable/para verificar;
- clustering de historias;
- comparación básica con Olé;
- recomendaciones explicables;
- preservación del último corte ante un corte degradado;
- fixture y pruebas automáticas.

## Probar

```powershell
python -m unittest discover -s tests -v
```

Todavía no se conectan Google Sheets, fuentes reales, Telegram ni IA. Es intencional: primero se valida el comportamiento editorial con datos controlados.


---

## Fase 2 · conexión a fuentes reales y a tu Google Sheet

Esta fase agrega la capa de integración alrededor del núcleo de fase 1, sin
tocar su lógica ya probada. Reutiliza el **mismo patrón de credenciales** del
monitor viejo (`GOOGLE_SERVICE_ACCOUNT_JSON` + `SHEET_ID` desde el entorno), así
que los secrets que ya tenés cargados sirven sin cambiar nada.

Piezas nuevas:

- `monitor/sources.py` — lee fuentes RSS reales y las convierte en `Article`.
- `monitor/sheets.py` — escribe las pestañas **Agenda** y **Snapshot** (crea la
  planilla si hace falta); degrada sin romper si faltan credenciales.
- `monitor/pipeline.py` — orquesta: fuentes → frescura → cluster → recomendación
  (comparando contra Olé) → escritura, preservando la Agenda anterior si el
  corte se degrada.
- `run_monitor.py` — el punto de entrada.
- `sources.json` — la lista de fuentes, editable sin tocar código.

### Probar en tu compu (sin riesgo)

Con Python 3.10+:

```bash
pip install -r requirements.txt
python run_monitor.py
```

Sin credenciales corre en **modo simulacro**: procesa las fuentes y te muestra
en pantalla qué habría escrito, sin tocar ninguna planilla. Para escribir de
verdad, exportá los secrets antes de correr:

```bash
export SHEET_ID="el-id-de-tu-planilla"
export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat tu-credencial.json)"
python run_monitor.py
```

(En PowerShell: `$env:SHEET_ID="..."` y `$env:GOOGLE_SERVICE_ACCOUNT_JSON=Get-Content tu-credencial.json -Raw`.)
Acordate de compartir la planilla con el email de la service account (permiso
Editor), igual que en el monitor viejo.

### Correr en la nube (GitHub Actions)

`.github/workflows/monitor.yml` corre `run_monitor.py` cada hora con los mismos
secrets del repo (`GOOGLE_SERVICE_ACCOUNT_JSON`, `SHEET_ID`). Subís el repo,
cargás esos dos secrets en Settings → Secrets → Actions, y lo disparás a mano
desde la pestaña Actions para probar.

### Una decisión de diseño importante (fuentes de agregador)

El núcleo distingue fechas **certificables** (metadata directa de la nota, RSS
propio) de fechas de **agregador** (Google News), que marca como
`para_verificar` y **no** deja entrar al resumen. Es el corazón de la fase 1.

Por eso los defaults de `sources.json` usan feeds **directos** (con fecha
confiable) y no fuentes de Google News. Las fuentes argentinas del monitor viejo
se leen vía búsqueda de Google News: entran a `sources.json` bajo
`feeds_agregador_desactivados` porque, tal como están, sus fechas no pasan el
filtro de frescura. Para incorporarlas como fuentes de primera clase falta el
paso de **enriquecimiento de fecha**: seguir el link de cada nota y leer su
`datePublished` real (JSON-LD/OpenGraph). Ese es el próximo incremento natural
(fase 2.1) y es justo lo que el núcleo ya sabe clasificar como `confirmada`.

### Fase 2.1 · enriquecimiento de fecha (fuentes argentinas)

Las fuentes argentinas (TyC, ESPN, Infobae) se leen vía Google News, cuya fecha
es de agregador y el núcleo desconfía. El módulo `monitor/enrich.py` resuelve
esto: para cada nota de una fuente marcada con `"enrich": true` en `sources.json`,
sigue el link, abre la página real de la nota y extrae su `datePublished` desde
la metadata (JSON-LD → OpenGraph → `<time>`). Con esa fecha certificada, la nota
pasa de `para_verificar` a `confirmada` y entra al resumen.

Detalles de comportamiento:

- Hay un tope de notas a enriquecer por corrida (`enrich_cap`, 40 por defecto)
  para acotar el tiempo. Cada fetch tiene timeout y degrada solo: si una nota no
  resuelve (timeout, o un link de Google News que no redirige al medio), conserva
  su clasificación previa y no rompe la corrida.
- El resumen en pantalla informa, por fuente, cuántas notas quedaron `con fecha
  real`.
- Las fuentes directas (Guardian, BBC) no necesitan enriquecimiento: su RSS ya
  trae fecha confiable.

Nota honesta: algunos links de Google News no resuelven server-side al medio
original (devuelven una interstitial). Esas notas simplemente no se enriquecen y
quedan fuera del resumen, que es el comportamiento seguro. Cuántas resuelvan
depende del medio; se ve en el conteo `con fecha real` de cada corrida.
