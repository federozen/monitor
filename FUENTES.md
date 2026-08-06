# Estrategia de fuentes

## Jerarquía

1. RSS directo.
2. RSS alternativo.
3. Página de últimas noticias.
4. Sitemap.
5. Buscador del sitio.
6. Google News restringido al dominio como descubrimiento final.

Google News nunca certifica la fecha real y nunca cuenta como publisher original.

## Registro y salud

Cada fuente conserva ID, nombre, zona, canal, estado, cantidad de noticias, último contenido, latencia y error. La vista editorial traduce esos datos en `SALUDABLE`, `DEMORADA`, `SIN CONTENIDO` o `CAÍDA` y sugiere un respaldo.

## Incorporación

No sumar fuentes por volumen. Una fuente nueva debería probarse durante siete días y demostrar aporte único, confiabilidad y una tasa aceptable de respuestas.

## Corte degradado

Si responde menos del umbral configurado, no se reemplaza el último panorama completo. Solo se agregan novedades verificadas y no se interpretan ausencias como desapariciones.
