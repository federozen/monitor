# Parche 12.1.2 — fechas, cobertura de Olé y hallazgos

Este parche se instala sobre la versión 12.1.1 que ya está escribiendo en la Google Sheet nueva.

## Qué corrige

1. Recupera fechas reales desde metadata de artículos directos prioritarios.
2. No usa la hora de Google News como fecha de publicación.
3. Evita coincidencias falsas con Olé por compartir solamente un club o un nombre.
4. Separa hallazgos firmes de candidatos débiles.
5. Guarda trazabilidad de la fecha utilizada y su origen en las hojas técnicas.

## Instalación sin consola

1. Descomprimir el ZIP.
2. En GitHub abrir **Code → Add file → Upload files**.
3. Arrastrar todo el contenido interior del parche, conservando las carpetas.
4. Confirmar con **Commit changes** en la rama `main`.
5. Esperar que **Tests del monitor** termine en verde.
6. Ejecutar **Actions → Monitor deportivo - mesa editorial → Run workflow**.
7. Actualizar la misma Google Sheet.

No hace falta volver a ejecutar **Preparar hojas del monitor**, cambiar secretos, crear otra planilla ni modificar Google Cloud.

## Resultado esperado

- Las notas directas con `datePublished` o `dateModified` pueden entrar al corte cuando corresponda.
- Una fecha de listado que solo indica el día no se inventa como una hora precisa.
- “El Betis pulveriza al Arsenal” no se vincula con una nota sobre Vinicius solo por compartir “Arsenal”.
- El caso débil de Salah permanece como candidato técnico y no ocupa la hoja de hallazgos firmes.
- Una historia extraordinaria corroborada por más de una fuente puede seguir clasificándose como hallazgo.

La ejecución puede demorar algo más que antes porque consulta un máximo configurable de artículos. El valor predeterminado es 48.
