// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentResponseSchema`.

import 'assignment_source.dart';
import 'assignment_status.dart';

class Assignment {
  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String reservationId;
  final String participantId;
  final String? participantName;
  final String equineId;
  final String? equineName;
  final String? saddleId;
  final String? saddleLabel;
  final AssignmentStatus status;
  final AssignmentSource source;
  final List<String>? safetyFlags;
  final List<String>? validationWarnings;
  final String? notes;
  final bool? isActive;
  final String? assignedByUserId;
  final String? finalizedByUserId;
  final String? assignedAt;
  final String? finalizedAt;

  const Assignment({
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.reservationId,
    required this.participantId,
    this.participantName,
    required this.equineId,
    this.equineName,
    this.saddleId,
    this.saddleLabel,
    required this.status,
    required this.source,
    this.safetyFlags,
    this.validationWarnings,
    this.notes,
    this.isActive,
    this.assignedByUserId,
    this.finalizedByUserId,
    this.assignedAt,
    this.finalizedAt,
  });

  factory Assignment.fromJson(Map<String, dynamic> json) {
    return Assignment(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      reservationId: json['reservation_id'] as String,
      participantId: json['participant_id'] as String,
      participantName: json['participant_name'] as String?,
      equineId: json['equine_id'] as String,
      equineName: json['equine_name'] as String?,
      saddleId: json['saddle_id'] as String?,
      saddleLabel: json['saddle_label'] as String?,
      status: (json['status'] as String).toAssignmentStatus(),
      source: (json['source'] as String).toAssignmentSource(),
      safetyFlags: (json['safety_flags'] as List<dynamic>?)?.cast<String>(),
      validationWarnings: (json['validation_warnings'] as List<dynamic>?)
          ?.cast<String>(),
      notes: json['notes'] as String?,
      isActive: json['is_active'] as bool?,
      assignedByUserId: json['assigned_by_user_id'] as String?,
      finalizedByUserId: json['finalized_by_user_id'] as String?,
      assignedAt: json['assigned_at'] as String?,
      finalizedAt: json['finalized_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'reservation_id': reservationId,
    'participant_id': participantId,
    'participant_name': participantName,
    'equine_id': equineId,
    'equine_name': equineName,
    'saddle_id': saddleId,
    'saddle_label': saddleLabel,
    'status': status.toJson(),
    'source': source.toJson(),
    'safety_flags': safetyFlags,
    'validation_warnings': validationWarnings,
    'notes': notes,
    'is_active': isActive,
    'assigned_by_user_id': assignedByUserId,
    'finalized_by_user_id': finalizedByUserId,
    'assigned_at': assignedAt,
    'finalized_at': finalizedAt,
  };
}
