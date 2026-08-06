# Desplegar en Streamlit Community Cloud

1. Entrá a Streamlit Community Cloud con la cuenta vinculada a GitHub.
2. Elegí `Create app` y seleccioná el repositorio privado.
3. Branch: `main`.
4. Main file: `app.py`.
5. En `Advanced settings → Secrets`, pegá:

```toml
GOOGLE_SERVICE_ACCOUNT_JSON = '''{JSON_COMPLETO}'''
SHEET_ID = "ID_DE_LA_PLANILLA_NUEVA"
SHEET_PREFIX = ""

# Solo para el botón pago:
ANTHROPIC_API_KEY = ""

# Solo para disparar GitHub Actions desde la app:
GITHUB_TOKEN = ""
GITHUB_REPO = "usuario/repositorio"
GITHUB_WORKFLOW = "vigia.yml"
GITHUB_REF = "main"
```

6. Desplegá.

La app lee la misma Google Sheet nueva. Recargarla no llama a Anthropic. El informe ampliado exige confirmación y botón; regenerarlo requiere una segunda confirmación.
