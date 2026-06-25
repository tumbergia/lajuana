import 'reservation_timeline_photo.dart';

/// Entrada unificada de la bitácora de una reserva.
class ReservationTimelineEntry {
  const ReservationTimelineEntry({
    required this.id,
    required this.source,
    required this.kind,
    required this.happenedAt,
    required this.title,
    this.description,
    this.actorName,
    this.actorRole,
    this.editable = false,
    this.deletable = false,
    this.relatedParticipantId,
    this.serviceLogId,
    this.photos = const [],
    this.photosTotal = 0,
  });

  final String id;
  final String source;
  final String kind;
  final DateTime happenedAt;
  final String title;
  final String? description;
  final String? actorName;
  final String? actorRole;
  final bool editable;
  final bool deletable;
  final String? relatedParticipantId;
  final String? serviceLogId;
  final List<ReservationTimelinePhoto> photos;
  final int photosTotal;
}
