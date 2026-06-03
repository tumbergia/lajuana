import '../gen/reservation_rules.dart' as gen;

/// Domain model for reservation configuration rules.
///
/// Wraps [gen.ReservationRules] and provides typed defaults
/// for business logic that runs before API calls.
class ReservationRules {
  const ReservationRules({
    required this.minDaysInAdvance,
    this.requirePaymentProofForConfirmation,
    this.reservationDraftTtlMinutes,
    this.minAge,
    this.maxAge,
  });

  factory ReservationRules.fromGen(gen.ReservationRules source) {
    return ReservationRules(
      minDaysInAdvance: source.minDaysInAdvance,
      requirePaymentProofForConfirmation:
          source.requirePaymentProofForConfirmation,
      reservationDraftTtlMinutes: source.reservationDraftTtlMinutes,
      minAge: source.minAge,
      maxAge: source.maxAge,
    );
  }

  final int minDaysInAdvance;
  final bool? requirePaymentProofForConfirmation;
  final int? reservationDraftTtlMinutes;
  final int? minAge;
  final int? maxAge;
}
