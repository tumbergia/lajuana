/// Modelo de dominio para una entrada del timeline de un equino.
class EquineTimelineEntry {
  const EquineTimelineEntry({
    required this.id,
    required this.source,
    required this.eventType,
    required this.happenedAt,
    required this.title,
    this.reservationId,
    this.notes,
    this.severity,
    this.affectsAvailability = false,
    this.syncPending = false,
  });

  final String id;
  final String source;
  final String eventType;
  final DateTime happenedAt;
  final String title;
  final String? reservationId;
  final String? notes;
  final String? severity;
  final bool affectsAvailability;
  final bool syncPending;
}
