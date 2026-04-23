# Mobile Auth v1 (Offline-First)

Fecha: 2026-04-22

## Objetivo

Implementar Auth v1 con prioridad de operación local y Session Gate como punto de entrada.

## Flujo de alto nivel

- `SessionGate -> Login` si no hay sesión local válida.
- `SessionGate -> Home` si sesión verificada o local no verificada.
- `Login -> Register` (visible solo con feature flag).
- `SessionView -> ChangePassword`.
- `Logout -> Login`.

## Capas implementadas

- Persistencia local SQLite:
  - `session_local`
  - `user_local`
- Infraestructura:
  - `AuthApiClient`
  - `SessionLocalDataSource`
  - `UserLocalDataSource`
  - `AuthRepository` (orquestación real HTTP + SQLite)
  - observador de conectividad
- Aplicación:
  - `BootstrapSessionUseCase`
  - `SignInUseCase`
  - `RefreshSessionUseCase`
  - `LogoutUseCase`
  - `RegisterUseCase`
  - `ChangePasswordUseCase`
  - `GetCurrentLocalSessionUseCase`
- Presentación:
  - `AuthController` (ChangeNotifier)
  - `SessionGateScreen`
  - `LoginScreen`
  - `RegisterScreen`
  - `SessionViewScreen`
  - `ChangePasswordScreen`

## Reglas operativas clave

- No se considera autenticado hasta completar `login + me`.
- Si no hay red y existe sesión local previa, se permite modo local degradado.
- Si no hay red y no existe sesión local, no se permite entrada.
- `refresh/me` con `401` invalida sesión local.
- `change-password` es online-only.
- Registro exitoso retorna a Login (sin login automático).
