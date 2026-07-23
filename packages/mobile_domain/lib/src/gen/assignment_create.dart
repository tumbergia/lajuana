// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `AssignmentCreateSchema`.

import 'assignment_status.dart';

class AssignmentCreate {
  final String reservationId;
  final String participantId;
  final String equineId;
  final String? saddleId;
  final AssignmentStatus? status;
  final String? notes;

  const AssignmentCreate({
    required this.reservationId,
    required this.participantId,
    required this.equineId,
    this.saddleId,
    this.status,
    this.notes,
  });

  factory AssignmentCreate.fromJson(Map<String, dynamic> json) {
    return AssignmentCreate(
      reservationId: json['reservation_id'] as String,
      participantId: json['participant_id'] as String,
      equineId: json['equine_id'] as String,
      saddleId: json['saddle_id'] as String?,
      status: json['status'] != null
          ? (json['status'] as String).toAssignmentStatus()
          : null,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'reservation_id': reservationId,
    'participant_id': participantId,
    'equine_id': equineId,
    'saddle_id': saddleId,
    'status': status?.toJson(),
    'notes': notes,
  };
}
