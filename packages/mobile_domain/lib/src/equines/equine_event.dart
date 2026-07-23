/// Modelo de dominio para un evento de cuidado/seguimiento del equino (RF14).
class EquineEvent {
  const EquineEvent({
    required this.id,
    required this.equineId,
    required this.eventType,
    required this.happenedAt,
    required this.title,
    this.description,
    this.severity,
    this.measuredWeightKg,
    this.nextDueAt,
    this.performedBy,
    this.affectsAvailability = false,
    this.resultingOperationalStatus,
    this.restUntil,
    this.syncPending = false,
  });

  final String id;
  final String equineId;
  final String eventType;
  final DateTime happenedAt;
  final String title;
  final String? description;
  final String? severity;
  final double? measuredWeightKg;
  final DateTime? nextDueAt;
  final String? performedBy;
  final bool affectsAvailability;
  final String? resultingOperationalStatus;
  final DateTime? restUntil;

  /// True cuando el evento está en cola local pendiente de sincronizar.
  final bool syncPending;
}

/// Payload para crear un evento desde la app móvil.
class EquineEventCreatePayload {
  const EquineEventCreatePayload({
    required this.eventType,
    required this.happenedAt,
    required this.title,
    this.description,
    this.severity,
    this.measuredWeightKg,
    this.nextDueAt,
    this.performedBy,
    this.affectsAvailability = false,
    this.resultingOperationalStatus,
    this.restUntil,
  });

  final String eventType;
  final DateTime happenedAt;
  final String title;
  final String? description;
  final String? severity;
  final double? measuredWeightKg;
  final DateTime? nextDueAt;
  final String? performedBy;
  final bool affectsAvailability;
  final String? resultingOperationalStatus;
  final DateTime? restUntil;

  Map<String, dynamic> toApiJson() {
    return {
      'event_type': eventType,
      'happened_at': happenedAt.toUtc().toIso8601String(),
      'title': title,
      if (description != null && description!.isNotEmpty)
        'description': description,
      if (severity != null) 'severity': severity,
      if (measuredWeightKg != null) 'measured_weight_kg': measuredWeightKg,
      if (nextDueAt != null)
        'next_due_at': nextDueAt!.toUtc().toIso8601String(),
      if (performedBy != null && performedBy!.isNotEmpty)
        'performed_by': performedBy,
      'affects_availability': affectsAvailability,
      if (resultingOperationalStatus != null)
        'resulting_operational_status': resultingOperationalStatus,
      if (restUntil != null) 'rest_until': restUntil!.toUtc().toIso8601String(),
      'source': 'mobile_app',
    };
  }
}
