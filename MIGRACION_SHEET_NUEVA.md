# Uso de la Google Sheet nueva

## Decisión adoptada

La Google Sheet creada durante la prueba inicial será la persistencia definitiva del monitor nuevo.

Se reutilizan:

- `SHEET_ID`;
- cuenta de servicio;
- permiso de Editor;
- repositorio privado de GitHub.

## Convivencia inicial

La planilla puede contener `Agenda` y `Snapshot`. El monitor nuevo crea hojas distintas, sin prefijo, y mantiene desactivadas las escrituras heredadas.

## Secuencia segura

1. Subir el código nuevo.
2. Mantener `AUTOMATION_ENABLED=false`.
3. Ejecutar `Preparar hojas del monitor`.
4. Ejecutar el monitor manualmente.
5. Comparar dos o tres cortes.
6. Activar el cron.
7. Archivar o borrar `Agenda` y `Snapshot` solamente cuando ya no sean útiles.

## Reversión

Cambiar `AUTOMATION_ENABLED=false` detiene las ejecuciones programadas. Las hojas y datos ya escritos permanecen disponibles para revisión.
