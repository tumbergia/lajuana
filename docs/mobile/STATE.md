# State Management Patterns

All state management in La Juana mobile is built on **`ValueNotifier` + `ChangeNotifier`** from `package:flutter/foundation.dart`. There is no third-party state management library.

## Core Pattern: `ChangeNotifier` Controllers

Every feature controller extends `ChangeNotifier` and exposes its state as public fields. Widgets listen via `AnimatedBuilder` (or `ListenableBuilder`).

```dart
class EquinesController extends ChangeNotifier {
  EquinesLoadState state = EquinesLoadState.idle;
  List<EquineRecord> items = const [];
  String? errorCode;
  String? errorMessage;

  Future<void> loadInitial() async {
    state = EquinesLoadState.loading;
    notifyListeners();
    try {
      // ... fetch from repository
      state = EquinesLoadState.success;
    } catch (e) {
      state = EquinesLoadState.error;
    }
    notifyListeners();
  }
}
```

**UI consumption:**
```dart
AnimatedBuilder(
  animation: controller,
  builder: (context, _) {
    if (controller.state == EquinesLoadState.loading) {
      return const AppCenteredLoader();
    }
    return ListView(/* ... */);
  },
);
```

## `ActionState<T>` Generic State Machine

Defined in `packages/mobile_core/lib/src/action_state.dart`.

Eliminates duplicated idle/loading/success/error patterns across action controllers.

```dart
enum ActionStatus { idle, loading, success, error }

class ActionState<T> {
  final ActionStatus status;
  final String? errorCode;
  final String? errorMessage;
  final T? data;
}
```

**Usage pattern:**
```dart
ActionState<String> approveState = ActionState.idle();

// Trigger action:
approveState = ActionState.loading();
notifyListeners();
approveState = await approveState.run(() => api.approve(id));
notifyListeners();
```

**Factory constructors:**
- `ActionState.idle()` — initial state
- `ActionState.loading()` — in progress
- `ActionState.success([data])` — completed with optional data
- `ActionState.error(code, message)` — failed

**Convenience getters:** `isIdle`, `isLoading`, `isSuccess`, `isError`

**`.run()` method:** Executes a `Future<T>` action, catches exceptions, and returns either `ActionState.success` or `ActionState.error`.

## Immutable State with `copyWith`

View models and domain models use immutable classes with `copyWith`. Example from `packages/mobile_domain/`:

```dart
class Equine {
  final String id;
  final String name;
  final EquineOperationalStatus operationalStatus;
  final bool isAvailable;
  // ...

  const Equine({required this.id, required this.name, /* ... */});

  Equine copyWith({String? name, EquineOperationalStatus? operationalStatus, /* ... */}) {
    return Equine(
      id: id,
      name: name ?? this.name,
      operationalStatus: operationalStatus ?? this.operationalStatus,
      // ...
    );
  }
}
```

Note: generated models (`packages/mobile_domain/lib/src/gen/`) do **not** include `copyWith` — solo tienen `fromJson`/`toJson`. Las clases manuales de dominio (`ReservationDetail`, `Equine` en `lib/src/`) sí lo implementan cuando es necesario.

## Controller Pattern with `_emit()`

Most controllers follow an **explicit state transition** pattern rather than a formal `_emit()` method (the equivalent is manual field mutation + `notifyListeners()`):

```dart
void _startLoading() {
  _clearError();
  isLoading = true;
  notifyListeners();
}

void _stopLoading() {
  isLoading = false;
  notifyListeners();
}

void _applySnapshot(AuthSessionSnapshot snapshot) {
  authState = snapshot.authState;
  currentUser = snapshot.currentUser;
  hasLocalSession = snapshot.hasLocalSession;
}
```

Example from `AuthController` in `features/auth/presentation/auth_controller.dart`. The `AuthController` uses this pattern extensively for all auth operations (login, logout, refresh, register, password change).

## `AnimatedBuilder` with `Listenable.merge`

When a widget needs to react to multiple controllers, `Listenable.merge` combines them:

```dart
AnimatedBuilder(
  animation: Listenable.merge([widget.authController, _shellNav]),
  builder: (context, _) {
    // React to changes from either authController or shellNav
    final canReachBackend =
        widget.authController.networkStatus.canReachBackend;
    // ...
  },
);
```

Example from `AuthenticatedShell` (`app/shell/authenticated_shell.dart`) — merges `AuthController` (session state, connectivity) with `ShellNavigationController` (current tab).

## Controller Examples by Feature

| Controller | File | State Fields |
|-----------|------|-------------|
| `AuthController` | `features/auth/presentation/auth_controller.dart` | `authState`, `currentUser`, `isLoading`, `isBootstrapping`, `networkStatus`, `errorCode`, `errorMessage` |
| `EquinesController` | `features/equines/presentation/controllers/equines_controller.dart` | `loadState`, `records`, `_filterMode` (private), `lastSyncedAt` |
| `SaddlesListController` | `features/saddles/presentation/controllers/saddles_list_controller.dart` | `loadState`, `items`, `showOnlyAvailable`, `lastSyncAt` |
| `ReservationsListController` | `features/reservations/presentation/controllers/reservations_list_controller.dart` | `loadState`, `items`, `searchQuery`, `filterGroup`, `lastSyncAt` |
| `DashboardController` | `features/dashboard/presentation/controllers/dashboard_controller.dart` | `loadState`, `todaySummary`, `weeklyTrend`, `lastSyncAt` |
| `ExperiencesController` | `features/catalogs/experiences/presentation/controllers/experiences_controller.dart` | `isInitialLoading`, `isRefreshing`, `isSyncing`, `error`, `items` |

## State Enums per Feature

Each list controller defines a load state enum:

```dart
enum SaddlesLoadState {
  idle, loading, refreshing, success, empty, error, offlineFromCache,
}
```

Common states across features:
- **`idle`** — not yet loaded
- **`loading`** — initial load
- **`refreshing`** — pull-to-refresh (keeps existing data visible)
- **`success`** — data available
- **`empty`** — loaded successfully but no data
- **`error`** — failed, no data to show
- **`offlineFromCache`** — network failed but cache fallback worked

## Best Practices

1. **Call `notifyListeners()` after every state mutation** that the UI needs to react to.
2. **Use `_startLoading()` / `_stopLoading()` pairs** for operations that show loading indicators.
3. **Guard `notifyListeners()` with `if (!mounted) return;`** after async gaps.
4. **Controllers are owned by modules** and created once at app startup (not per-screen).
5. **Dispose controllers explicitly** via `AppDependencies.dispose()`.
6. **Avoid deeply nested state** — keep controllers flat with named fields, not state objects.
