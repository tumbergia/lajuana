// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ServiceLogResponseSchema`.

import 'service_log_event_type.dart';
import 'service_log_photo.dart';

class ServiceLog {
  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String reservationId;
  final ServiceLogEventType eventType;
  final DateTime happenedAt;
  final String checkpointName;
  final String notes;
  final String relatedParticipantId;
  final String relatedEquineId;
  final String? createdBy;
  final List<ServiceLogPhoto>? photos;

  const ServiceLog({
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.reservationId,
    required this.eventType,
    required this.happenedAt,
    required this.checkpointName,
    required this.notes,
    required this.relatedParticipantId,
    required this.relatedEquineId,
    this.createdBy,
    this.photos,
  });

  factory ServiceLog.fromJson(Map<String, dynamic> json) {
    return ServiceLog(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      reservationId: json['reservation_id'] as String,
      eventType: (json['event_type'] as String).toServiceLogEventType(),
      happenedAt: DateTime.parse(json['happened_at'] as String),
      checkpointName: json['checkpoint_name'] as String,
      notes: json['notes'] as String,
      relatedParticipantId: json['related_participant_id'] as String,
      relatedEquineId: json['related_equine_id'] as String,
      createdBy: json['created_by'] as String?,
      photos: (json['photos'] as List<dynamic>?)
          ?.map((e) => ServiceLogPhoto.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'reservation_id': reservationId,
    'event_type': eventType.toJson(),
    'happened_at': happenedAt.toIso8601String(),
    'checkpoint_name': checkpointName,
    'notes': notes,
    'related_participant_id': relatedParticipantId,
    'related_equine_id': relatedEquineId,
    'created_by': createdBy,
    'photos': photos?.map((e) => e.toJson()).toList(),
  };
}
