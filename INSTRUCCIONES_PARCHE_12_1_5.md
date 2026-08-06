# Parche 12.1.5 — acciones limpias y Olé sincronizado

Este parche se construyó a partir de la exportación real `monitor (4).xlsx`.

## Diagnóstico de la corrida

La versión 12.1.4 resolvió la mayor parte de la agrupación:

- 58 clusters técnicos quedaron en 46 historias vivas.
- `RESUMEN_4H` mostró 12 temas.
- 37 de 37 historias consultadas obtuvieron una fecha utilizable.
- `OLE_HOY` reunió 50 registros.

Quedaron tres defectos concretos:

1. `ACCIONES` conservaba todas las versiones pendientes recalculadas dentro del mismo corte. La salida actual tenía 5 acciones útiles, pero la hoja acumulaba 23 filas; 18 correspondían a versiones anteriores del mismo corte.
2. Los números aislados todavía podían aparecer como novedades, por ejemplo “apareció el dato numérico 7”, aunque el 7 fuera la jornada del torneo.
3. `Control` informaba como última publicación de Olé las 16:45, mientras `OLE_HOY` ya contenía una publicación de las 20:52 y una actualización de las 22:56. Las métricas se calculaban antes de incorporar todas las vías de recolección.

## Cambios

- Una acción pendiente del corte vigente se reemplaza por su versión más nueva para la misma historia.
- Se conservan acciones abiertas de cortes anteriores y acciones marcadas como `HECHO` o `DESCARTADO`.
- Se eliminan marcadores genéricos de números aislados.
- “Fecha 4” o “fecha 7” deja de interpretarse como cambio de programación.
- Los cambios reales de horario, sede, postergación o reprogramación siguen detectándose.
- `Control` se sincroniza al final con la lista que efectivamente se escribe en `OLE_HOY`.
- Se agregan los campos:
  - `ole_ultima_actualizacion_hoy`
  - `ole_registros_finales`
- Versión del núcleo: `núcleo v29 · acciones limpias + métricas Olé sincronizadas`.

## Resultado esperado después de ejecutar

En una corrida equivalente a la exportación revisada:

- `ACCIONES` debería mostrar aproximadamente las 5 acciones actuales del resumen, más seguimientos legítimos de cortes anteriores si los hubiera.
- Ya no deberían permanecer como pendientes recomendaciones antiguas como Betis–Arsenal o Jódar cuando la corrida actual las bajó a panorama.
- El resumen no debería decir “apareció el dato numérico 7”.
- `Control` debería reflejar la última publicación y actualización que se ven en `OLE_HOY`.

## Instalación sin consola

1. Descomprimir el ZIP del parche.
2. En GitHub abrir `Code` → `Add file` → `Upload files`.
3. Arrastrar todo el contenido interior del parche, respetando las carpetas.
4. Confirmar con `Commit changes`.
5. Esperar que `Tests del monitor` termine en verde.
6. Ejecutar `Monitor deportivo - mesa editorial` desde `Actions`.
7. Actualizar la misma Google Sheet.

No hay que cambiar secretos, crear otra planilla ni volver a ejecutar la preparación de hojas.
