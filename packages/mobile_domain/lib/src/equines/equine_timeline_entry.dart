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
    this.measuredWeightKg,
    this.measuredHeightM,
    this.nextDueAt,
    this.performedBy,
    this.medicationName,
    this.dosage,
    this.labResultSummary,
    this.resultingOperationalStatus,
    this.restUntil,
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

  // Detalle estructurado del evento de cuidado (source == 'equine_event').
  // Se muestra en la bitácora para dar profundidad sin abrir cada evento.
  final double? measuredWeightKg;
  final double? measuredHeightM;
  final DateTime? nextDueAt;
  final String? performedBy;
  final String? medicationName;
  final String? dosage;
  final String? labResultSummary;
  final String? resultingOperationalStatus;
  final DateTime? restUntil;
}
