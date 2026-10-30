// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationProviderUpdateSchema`.

class ReservationProviderUpdate {
  final String? serviceLabel;
  final String? notes;
  final String? status;

  const ReservationProviderUpdate({this.serviceLabel, this.notes, this.status});

  factory ReservationProviderUpdate.fromJson(Map<String, dynamic> json) {
    return ReservationProviderUpdate(
      serviceLabel: json['service_label'] as String?,
      notes: json['notes'] as String?,
      status: json['status'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'service_label': serviceLabel,
    'notes': notes,
    'status': status,
  };
}
