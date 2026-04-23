# Auditoría externa: conectividad mobile ↔ API (La Juana)

Documento para revisión independiente. **Síntoma reportado:** la app móvil no completa peticiones al backend (timeouts, “sin conexión”, o fallos intermitentes).

**Repositorio:** `lajuana` — cliente Flutter en `apps/mobile`, API FastAPI en `apps/api`.

---

## 1. Resumen del flujo

1. Arranque: `main` → `bootstrap()` → `resolveApiBaseUrl()` → `runApp(LaJuanaApp(apiBaseUrl: …))`.
2. `AuthApiClient` usa `_baseUrl` fija + rutas relativas (`/auth/login`, etc.).
3. El repositorio de auth **no llama al API** si `ConnectivityState == offline` (login lanza `auth.requires_internet`).
4. Errores de socket/timeout se mapean a códigos `network.*`.

---

## 2. Resolución de la URL base del API

Archivo: [`apps/mobile/lib/app/api_base_url.dart`](../apps/mobile/lib/app/api_base_url.dart)

```dart
Future<String> resolveApiBaseUrl() async {
  const env = String.fromEnvironment('API_BASE_URL', defaultValue: '');
  if (env.isNotEmpty) {
    if (kIsWeb && _isWebUnsafeHost(env)) {
      debugPrint(
        'Ignorando API_BASE_URL=$env en web. Usa localhost/127.0.0.1.',
      );
    } else {
      return env;
    }
  }

  if (kIsWeb) {
    return 'http://localhost:8000/api/v1';
  }

  if (defaultTargetPlatform == TargetPlatform.android) {
    final android = await DeviceInfoPlugin().androidInfo;
    if (!android.isPhysicalDevice) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    if (kDebugMode) {
      debugPrint(
        'API: Android físico → 127.0.0.1. Para USB ejecuta: '
        'adb reverse tcp:8000 tcp:8000. '
        'En Wi‑Fi usa --dart-define=API_BASE_URL=http://<IP-LAN>:8000/api/v1',
      );
    }
    return 'http://127.0.0.1:8000/api/v1';
  }

  return 'http://127.0.0.1:8000/api/v1';
}
```

**Puntos de revisión:**

| Entorno | URL efectiva (sin `API_BASE_URL`) | Riesgo |
|--------|-------------------------------------|--------|
| Android emulador | `http://10.0.2.2:8000/api/v1` | Correcto si el API corre en el host en `:8000`. |
| Android físico | `http://127.0.0.1:8000/api/v1` | Solo llega al PC si `adb reverse tcp:8000 tcp:8000` (USB). En Wi‑Fi hay que pasar IP LAN vía `--dart-define`. |
| iOS simulador | `http://127.0.0.1:8000/api/v1` | Suele apuntar al Mac host. |
| iOS físico | Igual | Suele **no** alcanzar el Mac sin `API_BASE_URL` con IP del Mac en la LAN. |

**Contrato:** `API_BASE_URL` debe ser la **base completa hasta `/api/v1`** (sin barra final obligatoria en paths relativos del cliente).

---

## 3. Cliente HTTP y manejo de errores

Archivo: [`apps/mobile/lib/features/auth/infrastructure/remote/auth_api_client.dart`](../apps/mobile/lib/features/auth/infrastructure/remote/auth_api_client.dart)

```dart
class AuthApiClient {
  AuthApiClient({http.Client? httpClient, required String baseUrl})
    : _http = httpClient ?? http.Client(),
      _baseUrl = baseUrl;
  // ...
  Future<http.Response> _execute(Future<http.Response> Function() block) async {
    try {
      return await block().timeout(const Duration(seconds: 12));
    } on TimeoutException {
      throw AuthFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado',
      );
    } on SocketException {
      throw AuthFailure(code: 'network.unavailable', message: 'Sin conexión');
    } on HttpException {
      throw AuthFailure(code: 'network.http_error', message: 'Error de red');
    } on FormatException {
      throw AuthFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor',
      );
    }
  }
}
```

**Puntos de revisión:**

- Timeout fijo **12 s** → indica conexión colgada o host inalcanzable, no solo “lento”.
- `SocketException` → mensaje **“Sin conexión”** aunque el fallo sea “host equivocado” o “conexión rechazada” (ambigüedad UX/diagnóstico).

---

## 4. Conectividad (capa distinta del TCP)

Archivo: [`apps/mobile/lib/features/auth/infrastructure/connectivity_service.dart`](../apps/mobile/lib/features/auth/infrastructure/connectivity_service.dart)

```dart
  Future<ConnectivityState> current() async {
    try {
      final result = await _connectivity.checkConnectivity();
      return _map(result);
    } on MissingPluginException {
      return _assumeOnline;
    } catch (_) {
      return _assumeOnline;
    }
  }

  ConnectivityState _map(List<ConnectivityResult> list) {
    if (list.isEmpty) {
      return _assumeOnline;
    }
    final hasOnline = list.any((item) => item != ConnectivityResult.none);
    if (!hasOnline) return ConnectivityState.offline;
    final hasMobile = list.contains(ConnectivityResult.mobile);
    final hasWifi = list.contains(ConnectivityResult.wifi);
    if (hasMobile && !hasWifi) return ConnectivityState.unstable;
    return ConnectivityState.online;
  }
```

Archivo: [`apps/mobile/lib/features/auth/infrastructure/auth_repository_impl.dart`](../apps/mobile/lib/features/auth/infrastructure/auth_repository_impl.dart) (extracto login)

```dart
    if (connectivity == ConnectivityState.offline) {
      final hasLocal = await _tokenStorage.getSession() != null;
      if (hasLocal) {
        return enterLocalMode();
      }
      throw AuthFailure(
        code: 'auth.requires_internet',
        message: 'Requiere internet',
      );
    }

    final token = await _apiClient.login(email: email, password: password);
```

**Puntos de revisión:** el plugin solo refleja “radio/link”, no “Internet real”. Si `offline`, **no se intenta** el HTTP aunque el usuario tenga rutas alternativas.

---

## 5. Android: manifest y cleartext

Archivo: [`apps/mobile/android/app/src/main/AndroidManifest.xml`](../apps/mobile/android/app/src/main/AndroidManifest.xml)

```xml
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <application
        ...
        android:networkSecurityConfig="@xml/network_security_config">
```

Archivo: [`apps/mobile/android/app/src/main/res/xml/network_security_config.xml`](../apps/mobile/android/app/src/main/res/xml/network_security_config.xml)

```xml
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
</network-security-config>
```

**Puntos de revisión:** HTTP en claro permitido (adecuado solo para dev); producción debería usar TLS y política más restrictiva.

---

## 6. iOS: ATS

Archivo: [`apps/mobile/ios/Runner/Info.plist`](../apps/mobile/ios/Runner/Info.plist) (extracto)

```xml
		<key>NSAppTransportSecurity</key>
		<dict>
			<key>NSAllowsLocalNetworking</key>
			<true/>
		</dict>
```

---

## 7. Makefile y `dart-define`

Archivo: [`Makefile`](../Makefile) (extracto)

```makefile
MOBILE_API_BASE_URL ?=
MOBILE_DART_DEFINES := $(if $(strip $(MOBILE_API_BASE_URL)),--dart-define=API_BASE_URL=$(MOBILE_API_BASE_URL),)

mobile-profile:
	cd apps/mobile && ... flutter run --profile $(MOBILE_DART_DEFINES)
```

**Hallazgo corregido en repo:** una versión anterior definía por defecto `MOBILE_API_BASE_URL=http://localhost:8000/api` (sin `/v1` y con `localhost` en el dispositivo). Eso generaba URLs del tipo `…/api/auth/login` en lugar de `…/api/v1/auth/login` y apuntaba al loopback del **teléfono**, no al PC.

**Checklist para el auditor:**

- [ ] `API_BASE_URL` incluye el sufijo **`/api/v1`**.
- [ ] En Android físico por USB: `adb reverse tcp:8000 tcp:8000` **o** IP LAN en `API_BASE_URL`.
- [ ] API escuchando en `0.0.0.0:8000` si el cliente usa IP LAN (`uvicorn ... --host 0.0.0.0`).
- [ ] En consola Flutter (debug): línea `API base URL: …` tras el arranque.

---

## 8. Backend: prefijo esperado

La API monta el router con prefijo configurable; por defecto equivale a **`/api/v1`** (ver `app/core/config.py`: `api_prefix`, `api_version` y `app/api/router.py`).

Las rutas de auth son del estilo **`POST /api/v1/auth/login`**. Cualquier `baseUrl` del cliente que omita `/v1` producirá **404** (no necesariamente timeout).

---

## 9. Logcat / diagnóstico sugerido (Android)

Buscar en el dispositivo/emulador:

- `API base URL:` (impreso por `bootstrap.dart` en modo debug).
- Errores de red antes del timeout (DNS, `ECONNREFUSED`, etc.).
- Mensajes IME / red no aplican directamente al HTTP saliente salvo proxies VPN.

---

## 10. Archivos relacionados (índice)

| Área | Ruta |
|------|------|
| Bootstrap + URL | `apps/mobile/lib/bootstrap/bootstrap.dart`, `apps/mobile/lib/main.dart` |
| App + cliente único | `apps/mobile/lib/app/app.dart` |
| README mobile | `apps/mobile/README.md` |
| API dev | `apps/api/README.md` |

---

*Generado para auditoría externa; el código citado corresponde al estado del repositorio en la fecha de elaboración de este documento.*
