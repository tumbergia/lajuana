import '../../../catalogs/data/catalog_sync_status.dart';

class CatalogReservationRules {
  const CatalogReservationRules({
    required this.minDaysInAdvance,
    required this.requirePaymentProofForConfirmation,
    required this.syncStatus,
    this.versionRemote,
    this.syncError,
    this.updatedAtRemote,
  });

  final int minDaysInAdvance;
  final bool requirePaymentProofForConfirmation;
  final CatalogSyncStatus syncStatus;
  final int? versionRemote;
  final String? syncError;
  final DateTime? updatedAtRemote;
}
