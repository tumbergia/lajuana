import 'assignment_status.dart';

/// Mirrors backend AssignmentResponseSchema.
class Assignment {
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
  final List<String> safetyFlags;
  final List<String> validationWarnings;
  final String? notes;
  final bool isActive;
  final String? assignedByUserId;
  final String? finalizedByUserId;
  final DateTime? assignedAt;
  final DateTime? finalizedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Assignment({
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
    this.safetyFlags = const [],
    this.validationWarnings = const [],
    this.notes,
    this.isActive = true,
    this.assignedByUserId,
    this.finalizedByUserId,
    this.assignedAt,
    this.finalizedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Assignment.fromJson(Map<String, dynamic> json) {
    return Assignment(
      id: json['id'] as String,
      reservationId: json['reservation_id'] as String,
      participantId: json['participant_id'] as String,
      participantName: json['participant_name'] as String?,
      equineId: json['equine_id'] as String,
      equineName: json['equine_name'] as String?,
      saddleId: json['saddle_id'] as String?,
      saddleLabel: json['saddle_label'] as String?,
      status: AssignmentStatus.fromApi(json['status'] as String),
      source: AssignmentSource.fromApi(json['source'] as String),
      safetyFlags: List<String>.from(json['safety_flags'] ?? []),
      validationWarnings: List<String>.from(json['validation_warnings'] ?? []),
      notes: json['notes'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      assignedByUserId: json['assigned_by_user_id'] as String?,
      finalizedByUserId: json['finalized_by_user_id'] as String?,
      assignedAt: json['assigned_at'] != null
          ? DateTime.parse(json['assigned_at'] as String)
          : null,
      finalizedAt: json['finalized_at'] != null
          ? DateTime.parse(json['finalized_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
