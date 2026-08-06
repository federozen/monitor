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
