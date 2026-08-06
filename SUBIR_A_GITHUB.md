# Subir el monitor desde el navegador

1. Descomprimir el ZIP.
2. Abrir la carpeta descomprimida.
3. En GitHub: Add file > Upload files.
4. Arrastrar el contenido interior, no la carpeta exterior.
5. Confirmar que se suba `.github/workflows/` con:
   - `setup_sheets.yml`
   - `vigia.yml`
   - `tests.yml`
6. Hacer Commit changes en `main`.
7. Ejecutar primero `Preparar hojas del monitor` y luego `Monitor deportivo - mesa editorial`.
8. Cuando ambos funcionen, desactivar el workflow viejo `Monitor deportivo (fase 2)`.
