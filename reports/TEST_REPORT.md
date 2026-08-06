# Reporte de pruebas

Fecha de validación: 5 de agosto de 2026.

## Resultado

- Pruebas ejecutadas: **42**
- Aprobadas: **42**
- Fallas: **0**
- Errores: **0**

Comando utilizado:

```text
python -m unittest discover -s tests -v
```

## Cobertura funcional destacada

- frescura confirmada, probable y para verificar;
- Google News no certifica la fecha real;
- exclusión de notas antiguas o reindexadas;
- conservación del último panorama bueno ante corte degradado;
- clustering por publisher original;
- cambios editoriales reales frente a mera suma de medios;
- separación entre notas publicadas y actualizadas hoy en Olé;
- hallazgos firmes frente a candidatos para explorar;
- acciones resueltas que no reaparecen sin un dato nuevo;
- igualdad entre encabezados y filas escritas en Sheets;
- nombres definitivos de hojas sin prefijo en la planilla nueva;
- configuración nativa sin depender de `Agenda`, `Snapshot` ni `Config` heredadas.

La salida completa está guardada en `reports/test_output.txt`.
