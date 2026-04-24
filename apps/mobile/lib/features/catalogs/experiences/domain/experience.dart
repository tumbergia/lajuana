import '../../../catalogs/data/catalog_sync_status.dart';

class CatalogExperience {
  const CatalogExperience({
    required this.id,
    required this.name,
    required this.slug,
    required this.description,
    required this.level,
    required this.isActive,
    required this.syncStatus,
    this.durationHours,
    this.durationDays,
    this.baseCapacity,
    this.remoteId,
    this.versionRemote,
    this.syncError,
    this.updatedAtRemote,
  });

  final String id;
  final String? remoteId;
  final String name;
  final String slug;
  final String description;
  final String level;
  final int? durationHours;
  final int? durationDays;
  final int? baseCapacity;
  final bool isActive;
  final CatalogSyncStatus syncStatus;
  final int? versionRemote;
  final String? syncError;
  final DateTime? updatedAtRemote;
}
