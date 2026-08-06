# Monitor Deportivo

Mesa editorial automática y asistente proactivo para un editor deportivo argentino.

Esta edición está preparada para usar **la Google Sheet nueva que ya fue creada y probada**. Usa el mismo `SHEET_ID` y la misma cuenta de servicio que hicieron funcionar la primera prueba. No requiere otra planilla, otra credencial ni consola.

## Qué crea en la planilla nueva

Hojas visibles:

- `RESUMEN_4H`: panorama gratuito de 0 a 40 temas reales del corte.
- `ACCIONES`: publicar, actualizar, verificar, profundizar o seguir, con estado editable.
- `OLE_HOY`: publicaciones y actualizaciones del día separadas.
- `COBERTURA_OLE`: temas y enfoques ya cubiertos para evitar repetición.
- `HALLAZGOS`: historias firmes, con noticiabilidad y confianza separadas.
- `FUENTES_EDITOR`: estado de las fuentes en lenguaje editorial.
- `BUZON_SOCIAL`: enlaces agregados manualmente sin API social paga.
- `PARTES_IA`: informes pagos generados únicamente mediante confirmación y botón.

Hojas técnicas ocultas:

- `Noticias`, `Temas`, `Fuentes`, `Control`, `Recomendaciones`, `Descubrimientos`, `Cambios`, `Resumen`, `Oportunidades`, `HISTORIAL_4H`, `AUDITORIA`, `CONFIGURACION`, `AgentLog` y otras hojas de memoria.

Las pestañas `Agenda` y `Snapshot` de la prueba inicial pueden permanecer durante la validación. Este código no las usa ni las modifica porque las escrituras heredadas están desactivadas.

## Arquitectura

1. GitHub Actions recolecta y procesa cada 30 minutos.
2. Google Sheets conserva memoria, decisiones y salidas.
3. Streamlit Community Cloud lee resultados y permite registrar decisiones.
4. Anthropic es opcional y solo se llama bajo demanda.

La app no hace scraping al abrirse, no publica en Olé y no entrena modelos.

## Estado de esta entrega

- 42 pruebas automáticas aprobadas.
- Nombres definitivos sin prefijo porque la planilla es nueva y está dedicada al monitor.
- Automatización programada desactivada hasta definir `AUTOMATION_ENABLED=true`.
- Fallas del componente editorial central hacen fallar el workflow, salvo que se habilite explícitamente un modo degradado.
- Incluye demo simulada de tres historias vivas y auditoría.

## Instalación sin consola

Seguí `SETUP_NO_TECNICO.md`. En síntesis:

1. Subí el contenido de este proyecto al repositorio privado.
2. Conservá los secrets `GOOGLE_SERVICE_ACCOUNT_JSON` y `SHEET_ID` que ya funcionan.
3. No crees `SHEET_PREFIX`; si existe, dejalo vacío o borralo.
4. Ejecutá manualmente `Preparar hojas del monitor`.
5. Ejecutá `Monitor deportivo - mesa editorial`.
6. Revisá las nuevas pestañas en la misma Google Sheet.
7. Después de dos o tres cortes correctos, activá el cron.

## Documentación

- `SETUP_NO_TECNICO.md`
- `CONFIGURAR_GOOGLE_SHEETS.md`
- `CONFIGURAR_GITHUB_ACTIONS.md`
- `DEPLOY_STREAMLIT.md`
- `MIGRACION_SHEET_NUEVA.md`
- `ARQUITECTURA.md`
- `MODELO_DATOS.md`
- `FUENTES.md`
- `CRITERIOS_EDITORIALES.md`
- `COMPORTAMIENTO_AGENTICO.md`
- `MATRIZ_DECISIONES.md`
- `PRUEBAS.md`
- `LIMITACIONES_CONOCIDAS.md`

## Seguridad

Nunca subas el JSON de Google, tokens ni claves al repositorio. Los ejemplos incluidos no contienen valores reales. La decisión editorial siempre queda en manos del editor.
