// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineTimelineEntrySchema`.

class EquineTimelineEntry {

  final String id;
  final source source;
  final String eventType;
  final DateTime happenedAt;
  final String title;
  final String? reservationId;
  final String? assignmentId;
  final String? participantId;
  final String? notes;
  final String? severity;
  final bool? affectsAvailability;

  const EquineTimelineEntry(
    {
    required this.id,
    required this.source,
    required this.eventType,
    required this.happenedAt,
    required this.title,
    this.reservationId,
    this.assignmentId,
    this.participantId,
    this.notes,
    this.severity,
    this.affectsAvailability,
    }
  );

  factory EquineTimelineEntry.fromJson(Map<String, dynamic> json) {
    return EquineTimelineEntry(
      id: json['id'] as String,
      source: source.fromJson(json['source'] as Map<String, dynamic>),
      eventType: json['event_type'] as String,
      happenedAt: DateTime.parse(json['happened_at'] as String),
      title: json['title'] as String,
      reservationId: json['reservation_id'] as String?,
      assignmentId: json['assignment_id'] as String?,
      participantId: json['participant_id'] as String?,
      notes: json['notes'] as String?,
      severity: json['severity'] as String?,
      affectsAvailability: json['affects_availability'] as bool?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'source': source,
    'event_type': eventType,
    'happened_at': happenedAt.toIso8601String(),
    'title': title,
    'reservation_id': reservationId,
    'assignment_id': assignmentId,
    'participant_id': participantId,
    'notes': notes,
    'severity': severity,
    'affects_availability': affectsAvailability,
  };

}
