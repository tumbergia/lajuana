// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineTimelineEntrySchema`.

class EquineTimelineEntry {

  final String id;
  final String eventType;
  final DateTime happenedAt;
  final String title;
  final String? reservationId;
  final String? notes;

  const EquineTimelineEntry(
    {
    required this.id,
    required this.eventType,
    required this.happenedAt,
    required this.title,
    this.reservationId,
    this.notes,
    }
  );

  factory EquineTimelineEntry.fromJson(Map<String, dynamic> json) {
    return EquineTimelineEntry(
      id: json['id'] as String,
      eventType: json['event_type'] as String,
      happenedAt: DateTime.parse(json['happened_at'] as String),
      title: json['title'] as String,
      reservationId: json['reservation_id'] as String?,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'event_type': eventType,
    'happened_at': happenedAt.toIso8601String(),
    'title': title,
    'reservation_id': reservationId,
    'notes': notes,
  };

}
