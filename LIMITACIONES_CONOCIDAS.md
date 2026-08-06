# Limitaciones conocidas

- El scraping depende de cambios de HTML y políticas de cada sitio.
- La similitud semántica es heurística y puede requerir ajuste editorial.
- Google Sheets es apropiado para un editor y este volumen, pero no para alta concurrencia.
- El aprendizaje actual es memoria de estados y feedback; no entrena un modelo automáticamente.
- Telegram permanece desactivado por defecto.
- El predictivo no está implementado: corresponde a una fase separada en Colab.
- La completitud de Olé Hoy depende de poder atravesar la frontera de medianoche y obtener fechas.
- No se incluyen credenciales, despliegues operativos ni activación automática.
- El enriquecimiento abre como máximo 48 artículos prioritarios por ejecución de forma predeterminada; el resto conserva la fecha disponible en el listado.
- Los enlaces modernos y opacos de Google News no se decodifican ni se presentan como fuentes primarias; quedan para verificar hasta encontrar una URL directa.
- Sitios con paywall, bloqueo antibot o metadata incompleta pueden seguir sin fecha verificable.
- La coincidencia con Olé es heurística y conservadora: ante duda prefiere `COINCIDENCIA_DUDOSA` o `NO_CUBIERTO` antes que vincular notas distintas.

