// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationProviderCreateSchema`.

import 'reservation_provider_status.dart';

class ReservationProviderCreate {

  final String providerId;
  final String? serviceLabel;
  final String? notes;
  final ReservationProviderStatus? status;

  const ReservationProviderCreate(
    {
    required this.providerId,
    this.serviceLabel,
    this.notes,
    this.status,
    }
  );

  factory ReservationProviderCreate.fromJson(Map<String, dynamic> json) {
    return ReservationProviderCreate(
      providerId: json['provider_id'] as String,
      serviceLabel: json['service_label'] as String?,
      notes: json['notes'] as String?,
      status: json['status'] != null ? (json['status'] as String).toReservationProviderStatus() : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'provider_id': providerId,
    'service_label': serviceLabel,
    'notes': notes,
    'status': status?.toJson(),
  };

}
