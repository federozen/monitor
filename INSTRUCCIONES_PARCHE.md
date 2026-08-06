# Parche 12.1.1 — ACCIONES y HALLAZGOS

Este parche corrige la primera ejecución real del monitor:

- unifica el identificador de historia entre `Temas`, `Recomendaciones`, `Cambios` y la mesa editorial;
- permite que las recomendaciones firmes lleguen a `ACCIONES`;
- hace que `HALLAZGOS` muestre los hallazgos firmes vigentes del radar, aunque no pertenezcan al bloque horario fijo de `RESUMEN_4H`;
- agrega dos pruebas de regresión.

## Instalación sin consola

1. Descomprimir este ZIP.
2. En GitHub, abrir la pestaña **Code** del repositorio.
3. Elegir **Add file → Upload files**.
4. Arrastrar todo el contenido interior de la carpeta descomprimida, conservando las carpetas `editorial_agents` y `tests`.
5. Confirmar **Commit changes**.
6. Esperar que **Tests del monitor** termine en verde.
7. Ejecutar manualmente **Monitor deportivo - mesa editorial**.
8. Actualizar Google Sheets.

No hace falta volver a crear hojas ni modificar los secrets.
