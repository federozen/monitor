# Parche 12.1.4 — historias vivas y criterio editorial

Este parche se instala sobre la versión 12.1.3 y usa la misma Google Sheet, los mismos secretos y los mismos workflows.

## Qué corrige

1. Une clusters duplicados del mismo hecho antes de generar recomendaciones.
2. Evita que Boca–Estudiantes, Messi–San Luis o Tigre–Belgrano ocupen varias filas con títulos distintos.
3. Reconoce una nota de Olé presente en el propio cluster y usa ese enlace antes que un parecido aproximado.
4. Impide coincidencias por palabras genéricas como “resultados en vivo” o por compartir el año 2026.
5. No ordena publicar historias internacionales rutinarias sin conexión argentina; esas siguen disponibles en HALLAZGOS.
6. Elimina cambios artificiales como “apareció el dato numérico 0”.
7. Recupera en OLE_HOY notas recientes capturadas por la fuente directa de Olé aunque la página de Últimas quede incompleta.

## Instalación sin consola

1. Descargar y descomprimir `parche_v12_1_4_historias_vivas.zip`.
2. En GitHub abrir `Code`.
3. Elegir `Add file` → `Upload files`.
4. Arrastrar todo el contenido interior del parche.
5. Confirmar con `Commit changes`.
6. Esperar que `Tests del monitor` termine en verde.
7. Ejecutar `Monitor deportivo - mesa editorial` mediante `Run workflow`.
8. Actualizar la misma Google Sheet.

No hay que volver a ejecutar `Preparar hojas del monitor`, cambiar credenciales ni crear otra planilla.

## Qué debería verse en el próximo corte

- Menos filas repetidas en RESUMEN_4H y ACCIONES.
- Una única historia viva para cada partido o hecho central.
- Menos `PUBLICAR AHORA` internacionales sin valor argentino claro.
- Enlaces de Olé más precisos.
- OLE_HOY con notas más cercanas a la hora real de la corrida.
- En Control: `clusters_tecnicos`, `historias_vivas` y `clusters_fusionados`.
