import 'package:mobile/features/catalogs/data/catalog_sync_status.dart';

class CatalogReservationRules {
  const CatalogReservationRules({
    required this.minDaysInAdvance,
    required this.requirePaymentProofForConfirmation,
    required this.reservationDraftTtlMinutes,
    required this.minAge,
    required this.maxAge,
    required this.syncStatus,
    this.versionRemote,
    this.syncError,
    this.updatedAtRemote,
  });

  final int minDaysInAdvance;
  final bool requirePaymentProofForConfirmation;
  final int reservationDraftTtlMinutes;
  final int minAge;
  final int maxAge;
  final CatalogSyncStatus syncStatus;
  final int? versionRemote;
  final String? syncError;
  final DateTime? updatedAtRemote;
}
