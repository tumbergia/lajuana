// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationCancelSchema`.

class ReservationCancel {

  final String? reason;

  const ReservationCancel(
    {
    this.reason,
    }
  );

  factory ReservationCancel.fromJson(Map<String, dynamic> json) {
    return ReservationCancel(
      reason: json['reason'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'reason': reason,
  };

}
