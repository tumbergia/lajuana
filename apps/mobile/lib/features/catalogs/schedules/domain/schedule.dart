import 'package:mobile/features/catalogs/data/catalog_sync_status.dart';
import 'schedule_status.dart';

class CatalogSchedule {
  const CatalogSchedule({
    required this.id,
    required this.experienceId,
    required this.date,
    required this.startTime,
    required this.isActive,
    required this.capacityTotal,
    required this.reservedSlots,
    required this.internalSlots,
    required this.blockedSlots,
    required this.availableSlots,
    required this.status,
    required this.customRequestOnly,
    required this.syncStatus,
    this.notes,
    this.remoteId,
    this.versionRemote,
    this.syncError,
    this.updatedAtRemote,
  });

  final String id;
  final String? remoteId;
  final String experienceId;
  final String date;
  final String startTime;
  final bool isActive;
  final int capacityTotal;
  final int reservedSlots;
  final int internalSlots;
  final int blockedSlots;
  final int availableSlots;
  final CatalogScheduleStatus status;
  final bool customRequestOnly;
  final String? notes;
  final CatalogSyncStatus syncStatus;
  final int? versionRemote;
  final String? syncError;
  final DateTime? updatedAtRemote;
}
