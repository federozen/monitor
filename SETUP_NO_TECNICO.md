# Instalación sin consola usando la planilla nueva existente

Esta guía parte de una situación ya comprobada:

- la Google Sheet nueva existe;
- está compartida con el `client_email` de la cuenta de servicio;
- `SHEET_ID` y `GOOGLE_SERVICE_ACCOUNT_JSON` ya funcionaron en GitHub Actions;
- la ejecución anterior quedó verde y creó `Agenda` y `Snapshot`.

No crees otra planilla ni otras credenciales.

## 1. Subir esta versión al repositorio

Descomprimí el ZIP. En GitHub abrí el repositorio privado y elegí:

`Add file → Upload files`

Arrastrá **el contenido de la carpeta descomprimida**, no el ZIP cerrado. Confirmá con `Commit changes`.

En la raíz deben verse, entre otros:

- `app.py`
- `vigia.py`
- `online_storage.py`
- `editorial_agents`
- `.github`
- `.streamlit`
- `requirements.txt`

GitHub suele ocultar visualmente el detalle de `.github`; podés abrir la carpeta y comprobar que exista `.github/workflows`.

## 2. Reutilizar los dos secrets que ya funcionan

En:

`Settings → Secrets and variables → Actions → Secrets`

Deben existir:

- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `SHEET_ID`

No cambies sus valores si la prueba anterior escribió correctamente en la planilla.

## 3. Variables de GitHub

En `Settings → Secrets and variables → Actions → Variables`, creá:

- `AUTOMATION_ENABLED` = `false`
- `AGENT_ENABLED` = `true`
- `HIDE_TECHNICAL_SHEETS` = `true`
- `ALLOW_EDITORIAL_DEGRADED` = `false`

No hace falta crear `SHEET_PREFIX`. Si ya existe con `V12_`, borralo o dejalo vacío. Así las hojas se llaman directamente `RESUMEN_4H`, `ACCIONES`, `OLE_HOY`, etcétera.

## 4. Crear las hojas nuevas en la misma planilla

Entrá a:

`Actions → Preparar hojas del monitor → Run workflow → Run workflow`

Cuando termine en verde, actualizá la Google Sheet. Deben aparecer las hojas editoriales nuevas.

Las pestañas `Agenda` y `Snapshot` pueden quedar. No interfieren y esta versión no escribe en ellas.

## 5. Ejecutar el monitor nuevo

Entrá a:

`Actions → Monitor deportivo - mesa editorial → Run workflow → Run workflow`

Esperá a que quede verde. Después actualizá la planilla y revisá:

1. `RESUMEN_4H`
2. `ACCIONES`
3. `OLE_HOY`
4. `COBERTURA_OLE`
5. `HALLAZGOS`
6. `FUENTES_EDITOR`

Que el workflow quede verde confirma que terminó; la calidad editorial se comprueba leyendo esas hojas y el estado del corte.

## 6. Validar antes de automatizar

Hacé dos o tres ejecuciones manuales separadas por al menos 30 minutos. Revisá:

- si detecta novedades reales;
- si evita notas viejas;
- si distingue publicado y actualizado en Olé;
- si las acciones son útiles;
- si los hallazgos tienen valor para Argentina;
- si `FUENTES_EDITOR` informa caídas.

## 7. Activar la ejecución automática

Después de validar, cambiá:

`AUTOMATION_ENABLED = true`

El monitor correrá cada 30 minutos dentro de la franja configurada. La computadora puede permanecer apagada.

## 8. Qué hacer con Agenda y Snapshot

No las borres durante las primeras pruebas. Cuando el monitor nuevo esté validado, podés:

- dejarlas como archivo histórico;
- renombrarlas `ANTIGUA_Agenda` y `ANTIGUO_Snapshot`;
- eliminarlas manualmente.

La eliminación no es necesaria para que el monitor nuevo funcione.
