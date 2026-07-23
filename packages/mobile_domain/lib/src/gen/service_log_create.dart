// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ServiceLogCreateSchema`.

import 'service_log_event_type.dart';
import 'service_log_photo_input.dart';

class ServiceLogCreate {
  final String reservationId;
  final ServiceLogEventType eventType;
  final DateTime happenedAt;
  final String? checkpointName;
  final String? notes;
  final String? relatedParticipantId;
  final String? relatedEquineId;
  final List<ServiceLogPhotoInput>? photos;

  const ServiceLogCreate({
    required this.reservationId,
    required this.eventType,
    required this.happenedAt,
    this.checkpointName,
    this.notes,
    this.relatedParticipantId,
    this.relatedEquineId,
    this.photos,
  });

  factory ServiceLogCreate.fromJson(Map<String, dynamic> json) {
    return ServiceLogCreate(
      reservationId: json['reservation_id'] as String,
      eventType: (json['event_type'] as String).toServiceLogEventType(),
      happenedAt: DateTime.parse(json['happened_at'] as String),
      checkpointName: json['checkpoint_name'] as String?,
      notes: json['notes'] as String?,
      relatedParticipantId: json['related_participant_id'] as String?,
      relatedEquineId: json['related_equine_id'] as String?,
      photos: (json['photos'] as List<dynamic>?)
          ?.map((e) => ServiceLogPhotoInput.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'reservation_id': reservationId,
    'event_type': eventType.toJson(),
    'happened_at': happenedAt.toIso8601String(),
    'checkpoint_name': checkpointName,
    'notes': notes,
    'related_participant_id': relatedParticipantId,
    'related_equine_id': relatedEquineId,
    'photos': photos?.map((e) => e.toJson()).toList(),
  };
}
