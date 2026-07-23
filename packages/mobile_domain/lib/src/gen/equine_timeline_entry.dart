// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineTimelineEntrySchema`.

import 'equine_timeline_entry_source.dart';

class EquineTimelineEntry {

  final String id;
  final EquineTimelineEntrySource source;
  final String eventType;
  final DateTime happenedAt;
  final String title;
  final String? reservationId;
  final String? assignmentId;
  final String? participantId;
  final String? notes;
  final String? severity;
  final bool? affectsAvailability;
  final String? measuredWeightKg;
  final String? measuredHeightM;
  final String? nextDueAt;
  final String? performedBy;
  final String? medicationName;
  final String? dosage;
  final String? labResultSummary;
  final String? resultingOperationalStatus;
  final String? restUntil;

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
    this.measuredWeightKg,
    this.measuredHeightM,
    this.nextDueAt,
    this.performedBy,
    this.medicationName,
    this.dosage,
    this.labResultSummary,
    this.resultingOperationalStatus,
    this.restUntil,
    }
  );

  factory EquineTimelineEntry.fromJson(Map<String, dynamic> json) {
    return EquineTimelineEntry(
      id: json['id'] as String,
      source: (json['source'] as String).toEquineTimelineEntrySource(),
      eventType: json['event_type'] as String,
      happenedAt: DateTime.parse(json['happened_at'] as String),
      title: json['title'] as String,
      reservationId: json['reservation_id'] as String?,
      assignmentId: json['assignment_id'] as String?,
      participantId: json['participant_id'] as String?,
      notes: json['notes'] as String?,
      severity: json['severity'] as String?,
      affectsAvailability: json['affects_availability'] as bool?,
      measuredWeightKg: json['measured_weight_kg'] as String?,
      measuredHeightM: json['measured_height_m'] as String?,
      nextDueAt: json['next_due_at'] as String?,
      performedBy: json['performed_by'] as String?,
      medicationName: json['medication_name'] as String?,
      dosage: json['dosage'] as String?,
      labResultSummary: json['lab_result_summary'] as String?,
      resultingOperationalStatus: json['resulting_operational_status'] as String?,
      restUntil: json['rest_until'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'source': source.toJson(),
    'event_type': eventType,
    'happened_at': happenedAt.toIso8601String(),
    'title': title,
    'reservation_id': reservationId,
    'assignment_id': assignmentId,
    'participant_id': participantId,
    'notes': notes,
    'severity': severity,
    'affects_availability': affectsAvailability,
    'measured_weight_kg': measuredWeightKg,
    'measured_height_m': measuredHeightM,
    'next_due_at': nextDueAt,
    'performed_by': performedBy,
    'medication_name': medicationName,
    'dosage': dosage,
    'lab_result_summary': labResultSummary,
    'resulting_operational_status': resultingOperationalStatus,
    'rest_until': restUntil,
  };

}
