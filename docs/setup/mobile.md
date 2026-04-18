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
