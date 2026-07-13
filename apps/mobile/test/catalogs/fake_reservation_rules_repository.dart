import 'package:mobile/features/catalogs/reservation_rules/data/reservation_rules_repository.dart';
import 'package:mobile/features/catalogs/reservation_rules/domain/reservation_rules.dart';

import 'data/catalog_sync_status_helpers.dart';
import 'fake_catalogs_repository.dart';

/// Fake [ReservationRulesRepository] for testing [ReservationRulesController].
class FakeReservationRulesRepository extends ReservationRulesRepository {
  FakeReservationRulesRepository({
    this.returnNull = false,
    this.throwOnGet = false,
    this.throwOnUpdate = false,
  }) : super(FakeCatalogsRepository());

  final bool returnNull;
  final bool throwOnGet;
  final bool throwOnUpdate;

  int getCallCount = 0;
  int updateCallCount = 0;

  static final _sampleRules = CatalogReservationRules(
    minDaysInAdvance: 1,
    requirePaymentProofForConfirmation: false,
    reservationDraftTtlMinutes: 30,
    minAge: 12,
    maxAge: 65,
    syncStatus: catalogSyncStatusSynced,
  );

  @override
  Future<CatalogReservationRules> get() async {
    getCallCount++;
    if (throwOnGet) throw Exception('Get error');
    if (returnNull) throw Exception('No rules found');
    return _sampleRules;
  }

  @override
  Future<void> update({
    required int minDaysInAdvance,
    required bool requirePaymentProofForConfirmation,
    required int reservationDraftTtlMinutes,
    required int minAge,
    required int maxAge,
  }) async {
    updateCallCount++;
    if (throwOnUpdate) throw Exception('Update error');
  }
}
