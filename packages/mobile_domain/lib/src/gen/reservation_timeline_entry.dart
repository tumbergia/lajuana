// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationTimelineEntrySchema`.

import 'reservation_timeline_entry_source.dart';
import 'service_log_photo.dart';

class ReservationTimelineEntry {

  final String id;
  final ReservationTimelineEntrySource source;
  final String kind;
  final DateTime happenedAt;
  final String title;
  final String? description;
  final String? actorName;
  final String? actorRole;
  final bool? editable;
  final bool? deletable;
  final String? relatedParticipantId;
  final String? serviceLogId;
  final List<ServiceLogPhoto>? photos;
  final int? photosTotal;

  const ReservationTimelineEntry(
    {
    required this.id,
    required this.source,
    required this.kind,
    required this.happenedAt,
    required this.title,
    this.description,
    this.actorName,
    this.actorRole,
    this.editable,
    this.deletable,
    this.relatedParticipantId,
    this.serviceLogId,
    this.photos,
    this.photosTotal,
    }
  );

  factory ReservationTimelineEntry.fromJson(Map<String, dynamic> json) {
    return ReservationTimelineEntry(
      id: json['id'] as String,
      source: (json['source'] as String).toReservationTimelineEntrySource(),
      kind: json['kind'] as String,
      happenedAt: DateTime.parse(json['happened_at'] as String),
      title: json['title'] as String,
      description: json['description'] as String?,
      actorName: json['actor_name'] as String?,
      actorRole: json['actor_role'] as String?,
      editable: json['editable'] as bool?,
      deletable: json['deletable'] as bool?,
      relatedParticipantId: json['related_participant_id'] as String?,
      serviceLogId: json['service_log_id'] as String?,
      photos: (json['photos'] as List<dynamic>?)
        ?.map((e) => ServiceLogPhoto.fromJson(e as Map<String, dynamic>)).toList(),
      photosTotal: json['photos_total'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'source': source.toJson(),
    'kind': kind,
    'happened_at': happenedAt.toIso8601String(),
    'title': title,
    'description': description,
    'actor_name': actorName,
    'actor_role': actorRole,
    'editable': editable,
    'deletable': deletable,
    'related_participant_id': relatedParticipantId,
    'service_log_id': serviceLogId,
    'photos': photos?.map((e) => e.toJson()).toList(),
    'photos_total': photosTotal,
  };

}
