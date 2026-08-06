# Reporte de pruebas — Monitor Deportivo 12.1.2

Fecha de validación: 2026-08-05 (America/Argentina/Buenos_Aires).

## Resultado

- Pruebas ejecutadas: 67
- Aprobadas: 67
- Fallas: 0
- Errores: 0
- Validación estructural del repositorio: aprobada
- Compilación de módulos Python: aprobada

## Regresiones específicas de 12.1.2

1. Extrae `datePublished` y `dateModified` desde JSON-LD.
2. Reconoce fechas en español con hora.
3. Una fecha sin hora permanece como `publisher_date_only`.
4. Enriquece artículos directos sin promover fechas de Google News.
5. Una fecha de día sin hora no entra al Resumen 4H.
6. Compartir solo “Arsenal” no vincula dos hechos diferentes.
7. Betis–Arsenal con los mismos equipos y el mismo resultado sí puede vincularse.
8. Una historia débil sostenida solo por nombres globales queda como candidato.
9. Una rareza deportiva corroborada por dos fuentes puede ser hallazgo firme.

## Reproducción sobre la exportación real

La exportación recibida contenía 345 noticias: 184 con una fecha parseable y 161 sin fecha. Con la lógica nueva:

- “El Betis pulveriza al Arsenal” no coincide con la nota de Olé sobre Vinicius y Arsenal.
- La historia de Salah no se presenta como hallazgo firme.
- Las notas sin hora exacta no reciben una hora inventada.

El número final de temas del siguiente corte dependerá de cuántos publishers expongan metadata directa y permitan acceder al artículo.
