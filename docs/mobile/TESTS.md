# Testing Patterns

All tests use `flutter_test`. There is no mocking framework — tests use **hand-written fake implementations** of repositories, API clients, and data sources.

## Test File Structure

Test files mirror the `lib/` structure:

```
test/
├── auth/
│   ├── auth_controller_test.dart
│   ├── auth_widget_test.dart
│   └── test_fakes.dart
├── catalogs/
│   ├── experiences_controller_test.dart
│   ├── experience_form_controller_test.dart
│   ├── reservation_rules_controller_test.dart
│   ├── emergency_contacts_controller_test.dart
│   └── data/
│       └── catalog_sync_status_helpers.dart
├── reservations/
│   ├── reservations_list_controller_test.dart
│   ├── reservation_detail_controller_test.dart
│   ├── reservation_mapper_test.dart
│   ├── reservation_detail_dto_test.dart
│   ├── payment_proof_actions_test.dart
│   └── reservations_repository_impl_test.dart
├── saddles/
│   ├── saddles_list_controller_test.dart
│   └── fake_saddles_repository.dart
├── equines/
│   ├── equine_controller_test.dart
│   └── equine_mapper_test.dart
├── assignments/
│   ├── assignment_board_controller_test.dart
│   └── assignment_board_screen_test.dart
├── dashboard/
│   └── dashboard_controller_test.dart
├── participants/
│   └── participants_controller_test.dart
├── connectivity/
│   └── network_status_resolver_test.dart
├── shell/
│   └── authenticated_shell_test.dart
├── utils/
│   └── fake_reservations_repository.dart
├── widget_test.dart
└── ...
```

Shared fakes across features live in `test/utils/` or `test/<feature>/fake_*.dart`.

### Package tests

```
packages/mobile_core/test/
└── date_utils_test.dart

packages/mobile_domain/test/
└── gen_models_test.dart
```

## Fake Implementations

Fakes implement the same abstract interface as production code but return controlled data. They replace mocks entirely.

### Pattern: Stateful Fake

```dart
class _FakeAuthRepository implements AuthRepository {
  final AuthSessionSnapshot _snapshot;
  bool _shouldFail = false;

  void failNext({AuthFailure? failure}) {
    _shouldFail = true;
    if (failure != null) _failure = failure;
  }

  @override
  Future<AuthSessionSnapshot> bootstrapSession() async {
    if (_shouldFail) {
      _shouldFail = false;
      throw _failure;
    }
    return _snapshot;
  }
}
```

### Pattern: Configurable Fake

```dart
class FakeReservationsRepository implements ReservationsRepository {
  FakeReservationsRepository({
    this.returnEmpty = false,
    this.remoteFails = false,
    this.cacheOnly = false,
  });

  Future<List<ReservationListItem>> listReservations(...) async {
    if (remoteFails) throw Exception('Remote error');
    if (returnEmpty) return [];
    return [/* test data */];
  }
}
```

## Controller Tests

Controllers are tested with fake repositories. Tests verify **state transitions** (idle → loading → success/error) and **edge cases** (empty data, network failure, cache fallback).

### Pattern: State Transition Test

```dart
void main() {
  late ReservationsListController controller;

  setUp(() {
    final repository = FakeReservationsRepository();
    controller = ReservationsListController(repository: repository);
  });

  tearDown(() => controller.dispose());

  group('loadInitial', () {
    test('transitions to loading then success with items', () async {
      expect(controller.state, ReservationsLoadState.idle);

      await controller.loadInitial();

      expect(controller.state, ReservationsLoadState.success);
      expect(controller.items, isNotEmpty);
      expect(controller.lastSyncAt, isNotNull);
    });

    test('handles network error with cache fallback', () async {
      repository = FakeReservationsRepository.cacheOnly();
      controller = ReservationsListController(repository: repository);

      await controller.loadInitial();

      expect(controller.state, ReservationsLoadState.offlineFromCache);
    });
  });
}
```

### Auth Controller Tests (`auth_controller_test.dart`)

Tests all auth operations: `appStarted`, `loginSubmitted`, `logoutRequested`, `refreshRequested`, `sessionExpired`, `registerSubmitted`, `changePasswordSubmitted`, `enterLocalSessionRequested`.

Each test verifies:
- Starting state (`authState`, `isLoading`)
- Loading state after action
- Success state with expected fields
- Error state with expected `errorCode`/`errorMessage`

## Repository Tests

Repository tests verify the **remote → cache → fallback** pattern by injecting fake API clients and local data sources.

### Pattern: API Fallback Test

```dart
void main() {
  group('listReservations', () {
    test('returns API data and caches it', () async {
      final api = _FakeApiClient(items: [testItem]);
      final local = _FakeLocalDataSource();
      final repo = ReservationsRepositoryImpl(apiClient: api, localDataSource: local);

      final result = await repo.listReservations();

      expect(result, isNotEmpty);
      expect(local.wasCached, isTrue);
    });

    test('falls back to cache when API fails', () async {
      final api = _FakeApiClient(shouldThrow: true);
      final local = _FakeLocalDataSource.withCachedData();
      final repo = ReservationsRepositoryImpl(apiClient: api, localDataSource: local);

      final result = await repo.listReservations();

      expect(result, isNotEmpty);
      expect(api.wasCalled, isTrue);
    });
  });
}
```

## Mapper Tests

Mapper tests verify **DTO → Domain** and **Domain → ViewModel** conversions with both full and minimal input data, and edge cases (unknown enum values, null fields).

### Pattern: Equine Mapper Test

```dart
void main() {
  group('EquineMapper.dtoToDomain', () {
    test('maps full DTO correctly', () {
      final dto = EquineDto(
        id: 'equine-1',
        name: 'Pegaso',
        species: 'mule',
        operationalStatus: 'available',
        experienceFit: 'beginner',
      );

      final result = EquineMapper.dtoToDomain(dto);

      expect(result.id, 'equine-1');
      expect(result.operationalStatus, EquineOperationalStatus.available);
      expect(result.experienceFit, EquineExperienceFit.beginner);
    });

    test('maps unknown operational status to unavailable', () {
      final dto = EquineDto(
        id: 'e5',
        name: 'Unknown',
        operationalStatus: 'invalid_value',
      );

      final result = EquineMapper.dtoToDomain(dto);

      expect(result.operationalStatus, EquineOperationalStatus.unavailable);
    });
  });
}
```

## Widget Tests

Widget tests are less common. Existing examples:
- `auth_widget_test.dart` — Login screen rendering and interaction
- `authenticated_shell_test.dart` — Shell layout and tab switching
- `assignment_board_screen_test.dart` — Assignment board rendering

## Running Tests

```bash
# All mobile tests
cd apps/mobile && flutter test

# Specific test file
flutter test test/auth/auth_controller_test.dart

# Package tests
cd packages/mobile_core && dart test
cd packages/mobile_domain && dart test
```

## Best Practices

1. **Use `setUp`/`tearDown`** to create fresh controllers and dispose them — avoids state leakage between tests.
2. **Test state transitions**, not just final state. Verify `idle → loading → success`.
3. **Test error paths**. Every controller test should have a "handles error" case.
4. **Fakes are per-test or per-group** — scoped classes inside `main()` to avoid cross-test pollution.
5. **Mapper tests cover both full and minimal input**, plus enum fallback for unknown values.
6. **Repository tests verify cache was written** after successful API response, and that cache is read when API fails.
7. **No `mockito`** — all fakes are hand-written, making tests self-contained and readable.
