// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineEventUpdateSchema`.

class EquineEventUpdate {

  final String? eventType;
  final String? happenedAt;
  final String? title;
  final String? description;
  final String? severity;
  final String? reservationId;
  final String? assignmentId;
  final String? participantId;
  final String? measuredWeightKg;
  final String? measuredHeightM;
  final String? nextDueAt;
  final String? performedBy;
  final String? medicationName;
  final String? dosage;
  final String? labResultSummary;
  final String? affectsAvailability;
  final String? resultingOperationalStatus;
  final String? restUntil;
  final String? source;

  const EquineEventUpdate(
    {
    this.eventType,
    this.happenedAt,
    this.title,
    this.description,
    this.severity,
    this.reservationId,
    this.assignmentId,
    this.participantId,
    this.measuredWeightKg,
    this.measuredHeightM,
    this.nextDueAt,
    this.performedBy,
    this.medicationName,
    this.dosage,
    this.labResultSummary,
    this.affectsAvailability,
    this.resultingOperationalStatus,
    this.restUntil,
    this.source,
    }
  );

  factory EquineEventUpdate.fromJson(Map<String, dynamic> json) {
    return EquineEventUpdate(
      eventType: json['event_type'] as String?,
      happenedAt: json['happened_at'] as String?,
      title: json['title'] as String?,
      description: json['description'] as String?,
      severity: json['severity'] as String?,
      reservationId: json['reservation_id'] as String?,
      assignmentId: json['assignment_id'] as String?,
      participantId: json['participant_id'] as String?,
      measuredWeightKg: json['measured_weight_kg'] as String?,
      measuredHeightM: json['measured_height_m'] as String?,
      nextDueAt: json['next_due_at'] as String?,
      performedBy: json['performed_by'] as String?,
      medicationName: json['medication_name'] as String?,
      dosage: json['dosage'] as String?,
      labResultSummary: json['lab_result_summary'] as String?,
      affectsAvailability: json['affects_availability'] as String?,
      resultingOperationalStatus: json['resulting_operational_status'] as String?,
      restUntil: json['rest_until'] as String?,
      source: json['source'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'event_type': eventType,
    'happened_at': happenedAt,
    'title': title,
    'description': description,
    'severity': severity,
    'reservation_id': reservationId,
    'assignment_id': assignmentId,
    'participant_id': participantId,
    'measured_weight_kg': measuredWeightKg,
    'measured_height_m': measuredHeightM,
    'next_due_at': nextDueAt,
    'performed_by': performedBy,
    'medication_name': medicationName,
    'dosage': dosage,
    'lab_result_summary': labResultSummary,
    'affects_availability': affectsAvailability,
    'resulting_operational_status': resultingOperationalStatus,
    'rest_until': restUntil,
    'source': source,
  };

}
