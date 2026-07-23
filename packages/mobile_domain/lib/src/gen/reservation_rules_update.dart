// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationRulesUpdateSchema`.

class ReservationRulesUpdate {

  final String? minDaysInAdvance;
  final String? requirePaymentProofForConfirmation;
  final String? reservationDraftTtlMinutes;
  final String? minAge;
  final String? maxAge;

  const ReservationRulesUpdate(
    {
    this.minDaysInAdvance,
    this.requirePaymentProofForConfirmation,
    this.reservationDraftTtlMinutes,
    this.minAge,
    this.maxAge,
    }
  );

  factory ReservationRulesUpdate.fromJson(Map<String, dynamic> json) {
    return ReservationRulesUpdate(
      minDaysInAdvance: json['min_days_in_advance'] as String?,
      requirePaymentProofForConfirmation: json['require_payment_proof_for_confirmation'] as String?,
      reservationDraftTtlMinutes: json['reservation_draft_ttl_minutes'] as String?,
      minAge: json['min_age'] as String?,
      maxAge: json['max_age'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'min_days_in_advance': minDaysInAdvance,
    'require_payment_proof_for_confirmation': requirePaymentProofForConfirmation,
    'reservation_draft_ttl_minutes': reservationDraftTtlMinutes,
    'min_age': minAge,
    'max_age': maxAge,
  };

}
