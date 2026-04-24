enum CatalogSyncStatus { synced, pending, conflict, rejected }

String catalogSyncStatusToDb(CatalogSyncStatus value) => switch (value) {
  CatalogSyncStatus.synced => 'synced',
  CatalogSyncStatus.pending => 'pending',
  CatalogSyncStatus.conflict => 'conflict',
  CatalogSyncStatus.rejected => 'rejected',
};

CatalogSyncStatus catalogSyncStatusFromDb(String raw) => switch (raw) {
  'pending' => CatalogSyncStatus.pending,
  'conflict' => CatalogSyncStatus.conflict,
  'rejected' => CatalogSyncStatus.rejected,
  _ => CatalogSyncStatus.synced,
};
