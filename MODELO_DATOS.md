# Modelo de datos

## Artículo

Identifica publisher original y canal de descubrimiento por separado. Conserva título, URL, fecha, tipo de fecha, confianza temporal, país, idioma, sección y evidencia.

## Historia viva

El cluster es la unidad editorial. Conserva artículos, primera aparición, última novedad, mejor fecha, cantidad de publishers, confirmación oficial, cambios y cobertura de Olé.

## Cambio

Guarda `antes`, `ahora`, evidencia y acción. Más publishers no constituye por sí solo un cambio editorial.

## Acción

Tiene un `ActionID` estable derivado de historia, acción y cambio real. Estados: `PENDIENTE`, `EN CURSO`, `HECHO`, `DESCARTADO`, `SEGUIR`. Una acción resuelta no reaparece mientras no cambie el hecho que la originó.

## Hallazgo

Separa:

- `Noticiabilidad`: rareza, consecuencia, conexión argentina, visual, récord, historia humana, conflicto, negocio o tecnología.
- `Confianza`: fecha directa, cantidad de publishers originales y calidad de evidencia.

Estados: `HALLAZGO FUERTE`, `HALLAZGO`, `CANDIDATO PARA EXPLORAR`.

## Corte

Identificado por ventana de cuatro horas en `America/Argentina/Buenos_Aires`. Puede ser completo o degradado.
