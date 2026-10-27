# QA responsive móvil

La ausencia de errores de layout en un tamaño no garantiza compatibilidad general. Antes de promover un AAB, prueba al menos esta matriz en modo claro y oscuro.

| Escenario | Viewport lógico | Escala de texto |
| --- | ---: | ---: |
| Teléfono pequeño | 320 x 568 | 1.0 y 1.3 |
| Android compacto | 360 x 640 | 1.0 y 1.3 |
| Teléfono moderno | 390 x 844 | 1.0 y 2.0 |
| Teléfono grande | 412 x 915 | 1.0 y 1.3 |
| Horizontal compacto | 640 x 360 | 1.0 y 1.3 |

## Flujos obligatorios

- Login, registro y recuperación de sesión local.
- Navegación inferior y menú Más.
- Listado y detalle de reservas.
- Formularios con el teclado abierto.
- Calendario y asignaciones.
- Analítica, gráficos y hojas inferiores.
- Carga y previsualización de fotos.
- Asistente de voz y permisos.

## Criterios de aprobación

- Ningún `RenderFlex overflow`, texto cortado sin alternativa o control fuera de pantalla.
- Todos los flujos se pueden completar con texto al 200%.
- Los controles interactivos conservan un objetivo táctil de al menos 44 x 44.
- El teclado no oculta el campo activo ni la acción principal.
- `SafeArea` protege contenido frente a notch y navegación del sistema.
- Horizontal permite desplazarse y volver sin perder estado.

Las pruebas automatizadas cubren el login en esta matriz y la navegación inferior estrecha. El resto requiere pruebas widget adicionales y el reporte de pre-lanzamiento de Play Console sobre dispositivos reales.

