// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ServiceLogUpdateSchema`.

class ServiceLogUpdate {

  final String? eventType;
  final String? happenedAt;
  final String? checkpointName;
  final String? notes;
  final String? relatedParticipantId;
  final String? relatedEquineId;
  final String? photos;

  const ServiceLogUpdate(
    {
    this.eventType,
    this.happenedAt,
    this.checkpointName,
    this.notes,
    this.relatedParticipantId,
    this.relatedEquineId,
    this.photos,
    }
  );

  factory ServiceLogUpdate.fromJson(Map<String, dynamic> json) {
    return ServiceLogUpdate(
      eventType: json['event_type'] as String?,
      happenedAt: json['happened_at'] as String?,
      checkpointName: json['checkpoint_name'] as String?,
      notes: json['notes'] as String?,
      relatedParticipantId: json['related_participant_id'] as String?,
      relatedEquineId: json['related_equine_id'] as String?,
      photos: json['photos'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'event_type': eventType,
    'happened_at': happenedAt,
    'checkpoint_name': checkpointName,
    'notes': notes,
    'related_participant_id': relatedParticipantId,
    'related_equine_id': relatedEquineId,
    'photos': photos,
  };

}
