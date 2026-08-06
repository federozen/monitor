# Google Sheets: configuración para la planilla nueva existente

## Conexión

La planilla ya quedó conectada durante la prueba inicial. Esta versión reutiliza:

- el mismo `SHEET_ID`;
- el mismo `GOOGLE_SERVICE_ACCOUNT_JSON`;
- el mismo permiso de Editor concedido al `client_email`.

No hay que volver a Google Cloud ni descargar otro JSON.

## Hojas visibles definitivas

- `RESUMEN_4H`
- `ACCIONES`
- `OLE_HOY`
- `COBERTURA_OLE`
- `HALLAZGOS`
- `FUENTES_EDITOR`
- `BUZON_SOCIAL`
- `PARTES_IA`

Las hojas técnicas se crean y ocultan automáticamente. Incluyen artículos, clusters, cambios, snapshots, logs, historial, configuración y auditoría.

## Pestañas de la prueba anterior

`Agenda` y `Snapshot` no son parte del monitor nuevo. Pueden conservarse temporalmente. Las variables `LEGACY_MEMORY_WRITES_ENABLED`, `LEGACY_ALERTS_ENABLED` y `LEGACY_OLE_DIGEST_ENABLED` quedan desactivadas en el workflow.

## Uso eficiente

El código evita lecturas celda por celda: carga rangos completos, cachea registros, reemplaza tablas por lote y aplica reintentos con backoff ante errores de cuota.
