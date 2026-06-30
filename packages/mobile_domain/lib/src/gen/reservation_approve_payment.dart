// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationApprovePaymentSchema`.

class ReservationApprovePayment {

  final String? note;

  const ReservationApprovePayment(
    {
    this.note,
    }
  );

  factory ReservationApprovePayment.fromJson(Map<String, dynamic> json) {
    return ReservationApprovePayment(
      note: json['note'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'note': note,
  };

}
