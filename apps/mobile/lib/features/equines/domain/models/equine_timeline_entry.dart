/// Modelo de dominio para una entrada del timeline de un equino.
class EquineTimelineEntry {
  const EquineTimelineEntry({
    required this.id,
    required this.eventType,
    required this.happenedAt,
    required this.title,
    this.reservationId,
    this.notes,
  });

  final String id;
  final String eventType;
  final DateTime happenedAt;
  final String title;
  final String? reservationId;
  final String? notes;
}
