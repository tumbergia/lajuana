# Mobile App

Aplicación Flutter principal de La Juana.

## Comandos

```bash
flutter pub get
flutter run
flutter test
```

## API / red (desarrollo)

La URL del backend la resuelve [`AuthApiClient`](lib/features/auth/infrastructure/remote/auth_api_client.dart): variable de compilación `API_BASE_URL`, o valores por defecto:

| Plataforma | URL por defecto |
|------------|-----------------|
| Web | `http://localhost:8000/api/v1` |
| Android (emulador) | `http://10.0.2.2:8000/api/v1` (alias del host donde corre el API) |
| iOS / otros | `http://127.0.0.1:8000/api/v1` |

**Android físico por USB** (sin `API_BASE_URL`): la app usa `http://127.0.0.1:8000/api/v1` en el teléfono, que llega al API en tu PC si haces *port reverse*:

```bash
adb reverse tcp:8000 tcp:8000
```

**Dispositivo en Wi‑Fi** (o si no usas `adb reverse`): define la IP LAN del PC, por ejemplo:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1
```

Desde la raíz del repo también:

```bash
make mobile-run MOBILE_API_BASE_URL=http://192.168.1.10:8000/api/v1
```

**Servidor**: para que el móvil físico llegue al PC, el API debe escuchar en todas las interfaces, p. ej.:

```bash
cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Android e iOS permiten HTTP en claro para desarrollo local vía `network_security_config` y ATS (`NSAllowsLocalNetworking`). En producción conviene HTTPS.

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
