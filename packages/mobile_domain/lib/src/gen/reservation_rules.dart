// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationRulesSchema`.

class ReservationRules {

  final int minDaysInAdvance;
  final bool? requirePaymentProofForConfirmation;
  final int? reservationDraftTtlMinutes;
  final int? minAge;
  final int? maxAge;

  const ReservationRules(
    {
    required this.minDaysInAdvance,
    this.requirePaymentProofForConfirmation,
    this.reservationDraftTtlMinutes,
    this.minAge,
    this.maxAge,
    }
  );

  factory ReservationRules.fromJson(Map<String, dynamic> json) {
    return ReservationRules(
      minDaysInAdvance: json['min_days_in_advance'] as int,
      requirePaymentProofForConfirmation: json['require_payment_proof_for_confirmation'] as bool?,
      reservationDraftTtlMinutes: json['reservation_draft_ttl_minutes'] as int?,
      minAge: json['min_age'] as int?,
      maxAge: json['max_age'] as int?,
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
