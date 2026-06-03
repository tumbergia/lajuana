// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationConfirmSchema`.

class ReservationConfirm {

  final String? notes;

  const ReservationConfirm(
    {
    this.notes,
    }
  );

  factory ReservationConfirm.fromJson(Map<String, dynamic> json) {
    return ReservationConfirm(
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'notes': notes,
  };

}
