# Migración segura

1. Usá la Google Sheet nueva que ya fue conectada y probada.
2. Reutilizá `SHEET_ID` y `GOOGLE_SERVICE_ACCOUNT_JSON`.
3. No definas `SHEET_PREFIX`; debe quedar vacío.
4. Mantené `AUTOMATION_ENABLED=false`.
5. Ejecutá `Preparar hojas del monitor`.
6. Ejecutá dos o tres cortes manuales y comparalos.
7. Activá el cron solo después de validar la calidad.
8. `Agenda` y `Snapshot` pueden conservarse como archivo; el código nuevo no las modifica.

## Reversión

Cambiar `AUTOMATION_ENABLED=false` detiene el monitor programado sin borrar los datos ya generados.
