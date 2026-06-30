// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationProviderTabItemSchema`.

import 'provider_type.dart';
import 'reservation_provider_status.dart';

class ReservationProviderTabItem {

  final String reservationProviderId;
  final String reservationId;
  final String providerId;
  final String providerName;
  final ProviderType providerType;
  final ReservationProviderStatus status;
  final String serviceLabel;
  final String contactName;
  final String email;
  final String whatsappPhone;
  final String locationLabel;
  final String capacityNotes;
  final String operationalNotes;
  final String tariffNotes;
  final String notes;
  final String reservationCode;
  final String experienceName;
  final String scheduledDate;
  final int participantsCount;

  const ReservationProviderTabItem(
    {
    required this.reservationProviderId,
    required this.reservationId,
    required this.providerId,
    required this.providerName,
    required this.providerType,
    required this.status,
    required this.serviceLabel,
    required this.contactName,
    required this.email,
    required this.whatsappPhone,
    required this.locationLabel,
    required this.capacityNotes,
    required this.operationalNotes,
    required this.tariffNotes,
    required this.notes,
    required this.reservationCode,
    required this.experienceName,
    required this.scheduledDate,
    required this.participantsCount,
    }
  );

  factory ReservationProviderTabItem.fromJson(Map<String, dynamic> json) {
    return ReservationProviderTabItem(
      reservationProviderId: json['reservation_provider_id'] as String,
      reservationId: json['reservation_id'] as String,
      providerId: json['provider_id'] as String,
      providerName: json['provider_name'] as String,
      providerType: (json['provider_type'] as String).toProviderType(),
      status: (json['status'] as String).toReservationProviderStatus(),
      serviceLabel: json['service_label'] as String,
      contactName: json['contact_name'] as String,
      email: json['email'] as String,
      whatsappPhone: json['whatsapp_phone'] as String,
      locationLabel: json['location_label'] as String,
      capacityNotes: json['capacity_notes'] as String,
      operationalNotes: json['operational_notes'] as String,
      tariffNotes: json['tariff_notes'] as String,
      notes: json['notes'] as String,
      reservationCode: json['reservation_code'] as String,
      experienceName: json['experience_name'] as String,
      scheduledDate: json['scheduled_date'] as String,
      participantsCount: json['participants_count'] as int,
    );
  }

  Map<String, dynamic> toJson() => {
    'reservation_provider_id': reservationProviderId,
    'reservation_id': reservationId,
    'provider_id': providerId,
    'provider_name': providerName,
    'provider_type': providerType.toJson(),
    'status': status.toJson(),
    'service_label': serviceLabel,
    'contact_name': contactName,
    'email': email,
    'whatsapp_phone': whatsappPhone,
    'location_label': locationLabel,
    'capacity_notes': capacityNotes,
    'operational_notes': operationalNotes,
    'tariff_notes': tariffNotes,
    'notes': notes,
    'reservation_code': reservationCode,
    'experience_name': experienceName,
    'scheduled_date': scheduledDate,
    'participants_count': participantsCount,
  };

}
