# Regresión sobre `monitor (4).xlsx`

## Estado observado

- Noticias en snapshot: 292
- Clusters técnicos: 58
- Historias vivas: 46
- Clusters fusionados: 12
- Temas en `RESUMEN_4H`: 12
- Acciones visibles en `ACCIONES`: 23
- Acciones realmente vigentes según el resumen actual: 5
- Filas pendientes obsoletas del mismo corte: 18
- Fuentes correctas: 51 de 81 (63,0 %)
- Historias consultadas para fechas: 37
- Historias con fecha confirmada: 37
- Registros en `OLE_HOY`: 50
- Última publicación visible en `OLE_HOY`: 20:52
- Última actualización visible en `OLE_HOY`: 22:56
- Última publicación indicada por `Control`: 16:45

## Conclusión

La agrupación y la frescura temporal funcionaron. La principal regresión era de persistencia: `ACCIONES` acumulaba decisiones antiguas recalculadas dentro del mismo bloque de cuatro horas. La segunda era de observabilidad: `Control` seguía mostrando las métricas parciales del recolector de Últimas y no el resultado final de `OLE_HOY`.

El parche 12.1.5 corrige ambos puntos y elimina los marcadores numéricos sin contexto.
