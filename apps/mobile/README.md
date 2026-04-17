# Mobile App

Aplicación Flutter principal de La Juana.

## Comandos

```bash
flutter pub get
flutter run
flutter test
```

## Objetivo actual

Dejar una base mínima, estable y extensible para evolucionar hacia una app mobile-first y offline-first.

## Estructura

```
lib/
├─ main.dart            # Punto de entrada — delega a bootstrap()
├─ app/
│  ├─ app.dart          # Widget raíz (LaJuanaApp)
│  ├─ router.dart       # Configuración de rutas (pendiente)
│  └─ theme.dart        # Definición del tema (pendiente)
├─ bootstrap/
│  └─ bootstrap.dart    # Inicialización de bindings + runApp
└─ src/
   └─ .gitkeep          # Carpeta reservada para features
```
