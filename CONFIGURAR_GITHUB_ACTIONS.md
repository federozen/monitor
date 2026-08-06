# Configurar GitHub Actions

## Workflows

- `.github/workflows/tests.yml`: ejecuta las pruebas en cada push o pull request.
- `.github/workflows/vigia.yml`: procesa el monitor manualmente o cada 30 minutos.
- `.github/workflows/setup_sheets.yml`: crea y formatea las hojas en la planilla nueva, sin consola.

## Secrets obligatorios

- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `SHEET_ID`

Podés reutilizar los que ya hicieron funcionar la prueba anterior.

## Seguridad de activación

El cron solo corre si `AUTOMATION_ENABLED` vale `true`. La ejecución manual funciona aunque esté en `false`.

## Variables recomendadas

| Variable | Valor inicial |
|---|---|
| `AUTOMATION_ENABLED` | `false` |
| `AGENT_ENABLED` | `true` |
| `MIN_HEALTHY_SOURCE_RATIO` | `0.60` |
| `SCRAPE_MAX_WORKERS` | `5` |
| `GNEWS_MIN_INTERVAL_SECONDS` | `0.45` |
| `OLE_MAX_PAGES` | `8` |
| `EDITORIAL_SUMMARY_MAX_TOPICS` | `40` |
| `AGENT_TELEGRAM_MODE` | `off` |
| `HIDE_TECHNICAL_SHEETS` | `true` |
| `ALLOW_EDITORIAL_DEGRADED` | `false` |

No crees `SHEET_PREFIX`. Si existe, debe quedar vacío.

`ALLOW_EDITORIAL_DEGRADED=false` hace que una falla del módulo editorial central marque el workflow en rojo. La degradación normal por fuentes insuficientes se registra como `CORTE_DEGRADADO` y conserva el último panorama bueno.
