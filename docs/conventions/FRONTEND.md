# Frontend Conventions (Dart / Flutter)

## Config

| Setting | Value |
|---------|-------|
| Dart SDK | ^3.11.5 |
| Lint base | `package:flutter_lints/flutter.yaml` |
| Format | `dart format` |
| Analysis | `flutter analyze` (must pass with 0 errors) |
| Imports | `package:` imports preferred; relative imports reviewed in PR |

## Naming

| Element | Style | Example |
|---------|-------|---------|
| Files | `snake_case.dart` | `app_button.dart` |
| Classes | `PascalCase` | `AppButton` |
| Widgets | `PascalCase` | `AppTopBar` |
| Enums | `PascalCase` | `ReservationsLoadState` |
| Enum values | `camelCase` | `ReservationsLoadState.success` |
| Variables | `camelCase` | `_state`, `apiBaseUrl` |
| Private | `_leadingUnderscore` | `_emit()`, `_state` |
| Controllers | `*Controller` | `ReservationsListController` |
| State classes | `*State` | `ReservationsListState` |
| DTOs | `*Dto` | `ReservationListItemDto` |
| ViewModels | `*Record` | `EquineRecord` |

## Feature structure (Clean Architecture)

```
feature/
├── domain/
│   ├── models/          # Domain entities (pure Dart)
│   └── repositories/    # Abstract interfaces
├── infrastructure/
│   ├── remote/          # ApiClient + DTOs
│   ├── local/           # SQLite data sources
│   ├── repositories/    # Concrete implementations
│   └── mappers/         # DTO ↔ Domain
└── presentation/
    ├── controllers/     # ChangeNotifier + state
    ├── screens/         # Full-page widgets
    └── widgets/         # Feature-specific widgets
```

## State management

```dart
class ReservationsListController extends ChangeNotifier {
  ReservationsListState _state = const ReservationsListState();
  
  void _emit(ReservationsListState newState) {
    _state = newState;
    notifyListeners();
  }
}

class ReservationsListState {
  final List<ReservationRecord> items;
  final ReservationsLoadState loadState;
  
  const ReservationsListState({required this.items, ...});
  ReservationsListState copyWith({...});
}
```

- `ChangeNotifier` base class
- Immutable state with `copyWith()`
- `_emit()` single entry point for `notifyListeners()`
- `ActionState<T>` for async operations (idle/loading/success/error)

## Widget guidelines

- Stateless where possible
- `const` constructors when possible
- No business logic in widgets
- `Theme.of(context)` for colors/typography — never `Colors.*` directly
- Reusable widgets go to `packages/mobile_ui/`
- Single icon family: `material_symbols_icons`

## API client pattern

```dart
class ReservationsApiClient {
  Future<http.Response> _authorizedRequest({method, path, body}) async {
    // 1. Read access token
    // 2. Execute with timeout (12s)
    // 3. On 401 → refresh session + retry once
    // 4. Throw ReservationsApiFailure on error
  }
}
```

## Repository pattern (offline-first)

```dart
try {
  final dtos = await _apiClient.list();   // 1. Remote
  await _local.cache(payloads);            // 2. Cache
  return mapped;
} catch (_) {
  final cached = await _local.getCached(); // 3. Fallback
  return mapped;
}
```

## Imports

- `package:mobile/...` for feature code
- `package:mobile_ui/...`, `package:mobile_domain/...` for package code
- No `../../../../` relative imports

## Theme

- `AppTheme.light()` / `AppTheme.dark()` factory methods
- `ThemeExtension` for custom properties
- Design tokens in `packages/mobile_ui/`
