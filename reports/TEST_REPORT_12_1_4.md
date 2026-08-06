# Reporte de pruebas — 12.1.4

Fecha: 5 de agosto de 2026.

## Resultado

- Pruebas ejecutadas: 77
- Aprobadas: 77
- Fallas: 0
- Validación estructural del repositorio: correcta

## Regresiones agregadas

- Dos coberturas del mismo Boca–Estudiantes se convierten en una historia viva.
- Una consecuencia distinta, como la tabla anual, no se fusiona con el partido.
- Una nota directa de Olé gana frente a una coincidencia aproximada ajena.
- “Resultados en vivo 2026” no vincula partidos de equipos diferentes.
- Una historia extranjera rutinaria no genera PUBLICAR AHORA.
- Una actuación argentina relevante sigue siendo accionable.
- Los marcadores 0 y 1 no se describen como datos numéricos nuevos.
- Un tema meramente informativo no se etiqueta como imprescindible por estar entre los primeros.

## Prueba sobre la exportación real `monitor (3).xlsx`

La simulación determinística sobre los 61 clusters técnicos del archivo redujo el panorama a 49 historias vivas. Entre las fusiones detectadas estuvieron:

- ocho clusters relacionados con Boca–Estudiantes;
- tres clusters sobre Messi–Inter Miami–San Luis;
- dos clusters sobre Lisandro Martínez y la Ley de Tierras;
- dos clusters sobre Tigre–Belgrano;
- dos clusters sobre el interés de Barcelona en Julián Álvarez.

La prueba no vuelve a consultar internet ni modifica la planilla; usa únicamente los datos exportados.
