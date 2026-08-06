## 12.1.4 - 2026-08-05

- Agrega una segunda pasada de consolidación para convertir clusters técnicos duplicados en historias vivas.
- Fusiona con criterio conservador distintos ángulos del mismo partido o hecho y evita encadenamientos entre historias diferentes.
- Prioriza la evidencia directa de Olé contenida en el cluster sobre coincidencias aproximadas del inventario.
- Elimina falsos enlaces de cobertura producidos por expresiones genéricas como “resultados en vivo” y años compartidos.
- Separa el radar operativo de los hallazgos: una historia internacional rutinaria sin conexión argentina deja de generar `PUBLICAR AHORA`.
- Conserva como accionables las historias argentinas o globales con consecuencia suficiente.
- Normaliza acciones heredadas (`SUBIR YA`, `REDACTAR`, `RETOMAR`) antes de mostrarlas al editor.
- Deja de presentar los números 0 y 1 de un marcador como “dato numérico nuevo”.
- Clasifica como `IMPRESCINDIBLE` solo acciones firmes con prioridad editorial, no las primeras diez filas por posición.
- Suma las notas directas de Olé a `OLE_HOY` para recuperar publicaciones recientes que la paginación de Últimas pudiera omitir.
- Fuerza un recorrido mínimo de 12 páginas y 55 consultas de fecha en Olé.
- Agrega métricas de `clusters_tecnicos`, `historias_vivas` y `clusters_fusionados` a Control.
- Agrega siete pruebas de regresión; la suite completa alcanza 77 pruebas.

## 12.1.2 - 2026-08-05

- Agrega enriquecimiento acotado de fechas: abre solamente artículos directos priorizados y extrae `datePublished` / `dateModified` desde JSON-LD, metadatos y etiquetas `time`.
- Mantiene las horas de Google News como descubrimiento no verificable; nunca las usa para certificar actualidad.
- Reconoce formatos RFC-822, ISO, fechas numéricas y fechas en español con hora.
- Las fechas de día sin hora quedan como `publisher_date_only` y no ingresan artificialmente al Resumen 4H.
- Endurece la comparación con Olé: compartir un solo club o protagonista ya no alcanza para declarar cobertura.
- Exige coincidencia de entidades, hecho editorial y/o vocabulario distintivo antes de vincular una nota de Olé.
- Elimina de la salida visible los enlaces de Olé cuando la coincidencia no supera la validación.
- Separa mejor hallazgos firmes de candidatos: nombres globales o conexión argentina sin una señal editorial central ya no bastan.
- Amplía la trazabilidad técnica de Noticias y Temas con URL final, fecha publicada, fecha actualizada, confianza y origen.
- Agrega ocho pruebas de regresión específicas; la suite completa alcanza 67 pruebas.

## 12.1.1 - 2026-08-05

- Unifica el identificador de historia entre Temas, Recomendaciones, Cambios y la mesa editorial.
- Corrige ACCIONES vacía cuando existían recomendaciones firmes en la misma historia.
- HALLAZGOS pasa a mostrar los hallazgos firmes vigentes del radar, aunque no entren en el bloque fijo del RESUMEN_4H.
- Agrega pruebas de regresión para ambas fallas detectadas en la primera exportación real.

# Changelog

## 12.1 — Google Sheet nueva definitiva

- Configuró nombres de hojas sin prefijo para la planilla nueva dedicada al monitor.
- Reutiliza el mismo `SHEET_ID` y las mismas credenciales ya validadas.
- Eliminó de la app la dependencia de la hoja heredada `Config`.
- Agregó la hoja técnica nativa `CONFIGURACION`.
- Mantiene desactivadas todas las escrituras a `Agenda` y `Snapshot`.
- Renombró los workflows para que sean claros para un usuario sin consola.
- Actualizó toda la documentación de instalación.
- Agregó pruebas del nombre de pestañas y la configuración sin prefijo.

## 12.0 final

- Agregó auditoría persistente y visible en Streamlit.
- Separó noticiabilidad de confianza en hallazgos.
- Evitó que una fuente prestigiosa convierta un tema rutinario en hallazgo.
- Los candidatos ya no entran al resumen ni generan ideas firmes.
- Más publishers no se considera cambio si no existe un dato editorial nuevo.
- Mejoró agrupación de Olé para no mezclar servicios de clubes distintos.
- Separó `PUBLICADA_HOY` y `ACTUALIZADA_HOY`.
- Conserva acciones abiertas y no repite las resueltas sin un cambio real.
- Oculta hojas técnicas y mantiene visibles las editoriales.

## 12.1.3 — verificación por historia y candidatos visibles

- Segunda pasada de fechas distribuida por cluster para evitar que el presupuesto se concentre en varias notas del mismo tema.
- `Noticias` prioriza en el snapshot técnico las notas con metadata de artículo verificada.
- `HALLAZGOS` muestra también `CANDIDATO PARA EXPLORAR`, claramente marcado y con acción `VERIFICAR`; los candidatos no entran en `RESUMEN_4H` ni generan acciones firmes.
- Mayor profundidad predeterminada para recorrer `Olé Hoy` hasta acercarse a la medianoche real.
- Nuevos contadores de clusters consultados y confirmados en `Control`.
