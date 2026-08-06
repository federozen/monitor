# Reporte de pruebas — 12.1.5

## Resultado

- Pruebas ejecutadas: **81**
- Aprobadas: **81**
- Fallas: **0**
- Validación estructural del repositorio: **correcta**

## Regresiones nuevas cubiertas

1. Una jornada denominada “fecha 7” no se presenta como un dato numérico nuevo.
2. Un horario o una reprogramación explícita continúa detectándose como cambio real.
3. Varias acciones pendientes de una misma historia y un mismo corte se reemplazan por la versión actual.
4. Los seguimientos de cortes anteriores se conservan.
5. Las métricas de `Control` usan el rango final de publicación y actualización de `OLE_HOY`.

La salida completa está en `reports/test_output_12_1_5.txt`.
