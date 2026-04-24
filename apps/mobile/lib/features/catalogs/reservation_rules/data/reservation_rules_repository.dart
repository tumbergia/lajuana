import '../../data/catalogs_repository.dart';
import '../domain/reservation_rules.dart';

class ReservationRulesRepository {
  const ReservationRulesRepository(this._catalogsRepository);

  final CatalogsRepository _catalogsRepository;

  Future<CatalogReservationRules> get() =>
      _catalogsRepository.getReservationRules();

  Future<void> update({
    required int minDaysInAdvance,
    required bool requirePaymentProofForConfirmation,
  }) {
    return _catalogsRepository.updateReservationRules(
      minDaysInAdvance: minDaysInAdvance,
      requirePaymentProofForConfirmation: requirePaymentProofForConfirmation,
    );
  }
}
