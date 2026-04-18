# Setup mobile

## Comandos base

Desde la raíz del repo:

```bash
make mobile-run
```

O directamente:

```bash
cd apps/mobile
flutter pub get
flutter run
```

## Validación

```bash
cd apps/mobile
flutter test
```

En Windows, si aparece `Out of memory` en `kernel_snapshot_program`, ejecuta Flutter con mas heap de Dart:

```bash
cd apps/mobile
DART_VM_OPTIONS=--old_gen_heap_size=2048 flutter run
```

Si el shell no tiene `JAVA_HOME`, usa una ruta valida antes de compilar:

```bash
export JAVA_HOME="/c/Program Files/Java/jdk-17"
export PATH="$JAVA_HOME/bin:$PATH"
```

Los targets `make mobile-*` ya aplican por defecto `DART_VM_OPTIONS` y `JAVA_HOME` (configurable con `MOBILE_JAVA_HOME`).

## Calidad mínima

Desde la raíz del repo:

```bash
dart format --output=none --set-exit-if-changed apps/mobile/lib apps/mobile/test packages
cd apps/mobile && flutter analyze
cd packages/mobile_core && flutter analyze
cd packages/mobile_domain && flutter analyze
cd packages/mobile_mocks && flutter analyze
cd packages/mobile_ui && flutter analyze
cd apps/mobile && flutter test
```

## Branding de arranque

La app separa los assets de launcher icon y splash nativa dentro de `apps/mobile/assets/branding/`:

- `app_icon.png`: fuente maestra PNG para launcher icon.
- `app_icon.svg`: referencia vectorial de marca.
- `splash_logo.png`: asset dedicado para splash nativa.

Para regenerar recursos nativos despues de un cambio visual:

```bash
cd apps/mobile
flutter pub get
dart run flutter_launcher_icons
dart run flutter_native_splash:create
```

Si quieres volver al estado base generado por Flutter para splash:

```bash
cd apps/mobile
dart run flutter_native_splash:remove
```
