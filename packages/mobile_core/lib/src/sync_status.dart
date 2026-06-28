/// Estado de sincronizacion de una entidad local frente al backend.
///
/// Compartido por las features que usan el outbox offline (asignaciones,
/// saddles, ...). Espeja el enum `CatalogSyncStatus` de catalogos para que
/// ambos sistemas hablen el mismo idioma mientras se consolidan.
///
/// Se llama `EntitySyncStatus` (no `SyncStatus`) para no chocar con el
/// `SyncStatus` de sesion definido en `auth_enums.dart`.
enum EntitySyncStatus { synced, pending, conflict, rejected }

String entitySyncStatusToDb(EntitySyncStatus value) => switch (value) {
  EntitySyncStatus.synced => 'synced',
  EntitySyncStatus.pending => 'pending',
  EntitySyncStatus.conflict => 'conflict',
  EntitySyncStatus.rejected => 'rejected',
};

EntitySyncStatus entitySyncStatusFromDb(String? raw) => switch (raw) {
  'pending' => EntitySyncStatus.pending,
  'conflict' => EntitySyncStatus.conflict,
  'rejected' => EntitySyncStatus.rejected,
  _ => EntitySyncStatus.synced,
};
