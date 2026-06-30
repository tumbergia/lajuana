# Offline-First Patterns

La Juana mobile is designed as an **offline-first** application. The app remains fully functional without network connectivity, with data stored locally in SQLite databases and synchronized when connectivity is restored.

## SQLite Local Data Sources

Each feature maintains its own SQLite database via `sqflite`. Databases are initialized lazily on first access.

| Database | File | Tables |
|----------|------|--------|
| `AuthDatabase` | `features/auth/infrastructure/local/auth_database.dart` | `session_local`, `user_local` |
| `CatalogsDatabase` | `features/catalogs/data/catalogs_database.dart` | `experiences_local`, `reservation_rules_local`, `emergency_contacts_local`, `sync_queue`, `id_map`, `sync_cursors` |
| `EquinesDatabase` | `features/equines/infrastructure/local/equines_database.dart` | `equines_cache`, `equine_sync_meta` |

| `ReservationsDatabase` | `features/reservations/infrastructure/local/reservations_database.dart` | `reservations_list_cache`, `reservation_detail_cache` |
All databases follow a singleton pattern with a `static final instance` and lazy initialization:

```dart
class CatalogsDatabase {
  CatalogsDatabase._();
  static final CatalogsDatabase instance = CatalogsDatabase._();

  Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    // open database, run migrations, cache instance
  }
}
```

### Web Support

The web platform uses `sqflite_common_ffi_web` with `databaseFactoryFfiWebNoWebWorker` to avoid shared-worker dependency in dev mode.

## Repository Pattern: Remote → Cache → Fallback

Every repository implements a **3-tier fallback**:

1. Try remote (API call)
2. If success → cache response locally → return data
3. If failure → try local cache → return cached data or rethrow

### Example: `ReservationsRepositoryImpl`

```dart
class ReservationsRepositoryImpl implements ReservationsRepository {
  final ReservationsApiClient _apiClient;
  final ReservationsLocalDataSource _localDataSource;

  Future<List<ReservationListItem>> listReservations(...) async {
    try {
      // 1. Fetch from backend
      final dtos = await _apiClient.listReservations(...);
      // 2. Map to domain
      final items = dtos.map((d) => dtoToListItem(d)).toList();
      // 3. Cache for offline fallback
      await _localDataSource.cacheList(listPayloads);
      await _localDataSource.setLastSyncAt(DateTime.now());
      // 4. Apply local filters
      return _applyFilters(items, ...);
    } catch (_) {
      // 5. Network failed — try cache
      final cached = await _localDataSource.getCachedList();
      if (cached.isEmpty) rethrow;
      return cached.map((record) => dtoToListItem(record)).toList();
    }
  }
}
```

### Example: `SaddlesRepositoryImpl`

```dart
class SaddlesRepositoryImpl implements SaddlesRepository {
  final SaddlesApiClient _apiClient;

  Future<List<SaddleListItem>> listSaddles(...) async {
    try {
      return await _apiClient.listSaddles(...);
    } catch (_) {
      // No local cache yet — falls through to error in controller
      rethrow;
    }
  }
}
```

### Example: `EquineRepositoryImpl`

```dart
class EquineRepositoryImpl implements EquineRepository {
  final EquinesApiClient _apiClient;
  final EquinesDatabase _database;

  Future<List<Equine>> listEquines(...) async {
    try {
      final items = await _apiClient.listEquines(...);
      await _cacheEquines(items); // write to SQLite
      return items;
    } catch (_) {
      return _getCachedEquines(); // read from SQLite
    }
  }
}
```

## Sync Protocol Integration

The **Catalogs** feature has the most sophisticated offline sync, using a cursor-based sync protocol via `CatalogsRepository`.

### Sync Cursors

Each data stream has a cursor stored in `sync_cursors` table:
```sql
CREATE TABLE sync_cursors (
  stream TEXT PRIMARY KEY,
  cursor TEXT NOT NULL
);
```

Known streams: `experiences`, `config`, `reservations`, `participants`, `payment_proofs`, `assignments`, `logs`, `equines`, `providers`, `policies`.

### Bootstrap

When a stream has no cursor (first launch), `CatalogsRepository._bootstrap()` fetches all data from `GET /sync/bootstrap` and populates local tables + cursors in a single transaction.

### Pull Changes

`pullChanges()` sends current cursors to `POST /sync/pull` and receives incremental changes per stream. Each change is applied within a transaction (`_upsertExperienceFromServer`, `_upsertScheduleFromServer`, `_applyConfigChange`).

### Push Changes (Queue)

Offline-created/modified entities are **queued** in `sync_queue`:

```
sync_queue columns:
  operation_id, entity_type, operation_type, entity_local_id,
  entity_remote_id, base_version, idempotency_key,
  payload_json, status, error_code, error_message, created_at
```

The queue is flushed on connectivity via `flushQueue()`. Statuses:
- `pending` → ready to send
- `applied` → server accepted (removed from queue)
- `conflict` → version mismatch (can retry with `includeFailed: true`)
- `rejected` → server rejected

### Id Map

Local IDs (`local-experience-1700000000-123456`) are mapped to remote IDs via the `id_map` table during push, enabling offline-created entities to be referenced before they exist on the server.

### Auto Sync

The `AuthenticatedShell` triggers auto-sync when the backend becomes reachable after being unreachable:

```dart
if (canReachBackend && !_wasBackendReachable && widget.catalogsModule != null) {
  unawaited(widget.catalogsModule!.repository.autoSync());
}
```

## Connectivity Monitoring

### `ConnectivityPlusService` (`features/auth/infrastructure/connectivity/connectivity_service.dart`)

Wraps `connectivity_plus` to monitor the device's network link:

- `currentLinkType()` → returns `LinkType` enum (`offline`, `mobile`, `wifi`, `other`)
- `observeLinkType()` → stream of link type changes
- Web fallback: polls every 5 seconds via `currentLinkType()` (since `onConnectivityChanged` isn't available on web)

### `HttpBackendReachabilityService` (`features/auth/infrastructure/connectivity/backend_reachability_service.dart`)

Pings `GET /health` with a 3-second timeout to determine if the backend is actually reachable. Returns `BackendReachability` enum.

Distinguishes between "no network" (offline) and "network but backend down" to show appropriate banners.

### `NetworkStatusResolver` (`features/auth/infrastructure/connectivity/network_status_resolver.dart`)

Combines both services into a `NetworkStatus`:

```dart
class NetworkStatus {
  final LinkType linkType;
  final BackendReachability backendReachability;

  bool get canReachBackend => backendReachability == BackendReachability.reachable;
  bool get hasSomeLink => linkType != LinkType.offline;
}
```

Provides:
- `current()` — one-shot check
- `observe()` — stream that yields on link type changes and re-checks reachability

### Consumer: `AuthController`

`AuthController` subscribes to `NetworkStatusResolver.observe()` and exposes `networkStatus` as a public field. When link recovers and session is in `signedInLocalUnverified` state, it automatically attempts session refresh:

```dart
void _onNetworkStatus(NetworkStatus next) {
  networkStatus = next;
  notifyListeners();
  if (next.linkType != LinkType.offline &&
      authState == LocalAuthState.signedInLocalUnverified) {
    unawaited(refreshRequested());
  }
}
```

### Consumer: `ShellStatusRegion`

The shell renders status banners based on `networkStatus`:
- **Offline** → "Sin enlace de red"
- **Backend unreachable** → "Servidor no alcanzable"
- **Mobile data** → "Red movil"
- **Pending sync** → "Cambios pendientes"
- **Local session** → "Sesion local"
- **Session expired** → "Sesion requiere validacion"

## Offline UX States

- **Offline from cache**: List controllers have `state = SaddlesLoadState.offlineFromCache` when remote fails but local data is available.
- **Offline-restricted mode**: `authController.isOfflineRestricted` blocks online-only actions (e.g., payment processing).
- **Reconnect overlay**: `_ReconnectLoadingView` shown when the app is re-establishing session after backend becomes reachable.
