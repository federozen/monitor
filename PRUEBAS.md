# Pruebas

La suite se ejecuta con GitHub Actions mediante `.github/workflows/tests.yml`.

Cobertura actual: 40 pruebas unitarias y de integración con fixtures. Ver `reports/TEST_REPORT.md`.

Incluye controles de:

- antigüedad y fechas explícitas;
- Google News no certifica actualidad;
- RSS directo sí puede ser probable;
- corte degradado y snapshot preservado;
- Olé publicadas y actualizadas separadas;
- agrupación de Boca y River sin falsos clusters;
- más publishers no constituye un cambio por sí solo;
- hallazgo no depende solo de reputación;
- candidatos no generan recomendación firme;
- ActionID estable;
- auditoría de exclusiones.

También se incluye `scripts/run_demo.py`, que genera una salida end-to-end simulada sin red ni credenciales.
