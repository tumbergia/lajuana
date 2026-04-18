# Convenciones Flutter

## Reglas generales

1. La UI reusable no contiene lógica de negocio.
2. Los componentes deben consumir tema global.
3. Los playgrounds no son flujos productivos.
4. Las features deben tender a organización por capas:
   - presentation
   - application
   - domain
   - infrastructure

## Theming

- usar `Theme.of(context)`
- usar `ColorScheme`, `TextTheme` y `ThemeExtension`
- evitar `Colors.*` directos salvo casos excepcionales

## Widgets

Un widget reusable debe:
- tener una responsabilidad clara;
- evitar dependencias innecesarias;
- mantener parámetros controlados;
- no resolver demasiados patrones distintos a la vez.

## Arranque

- La splash nativa solo cubre el arranque del motor Flutter y debe ser estatica, minima y coherente con marca.
- La splash nativa no debe incluir animaciones ni loaders simulados.
- Si la app necesita bootstrap real, se implementa en una StartupScreen de Flutter, no en la splash nativa.
- El arranque debe priorizar estado local (configuracion, sesion, storage, colas pendientes) y no bloquear por red.
