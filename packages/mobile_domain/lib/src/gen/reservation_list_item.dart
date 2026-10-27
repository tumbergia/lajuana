// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationListItemSchema`.

import 'participant_form_status.dart';
import 'payment_status.dart';
import 'reservation_status.dart';

class ReservationListItem {
  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String code;
  final ReservationStatus status;
  final int participantCount;
  final PaymentStatus paymentStatus;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final bool? assistantDisabled;
  final String experienceId;
  final String? experienceName;
  final String? requestedDate;
  final String? scheduledDate;
  final String? expectedParticipantsCount;
  final int? participantsCompletedCount;
  final ParticipantFormStatus? participantFormStatus;
  final String? channel;
  final String? assignmentStatus;
  final int? assignmentsTotal;
  final int? assignmentsPending;
  final List<String>? assignmentBlockingReasons;

  const ReservationListItem({
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.code,
    required this.status,
    required this.participantCount,
    required this.paymentStatus,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    this.assistantDisabled,
    required this.experienceId,
    this.experienceName,
    this.requestedDate,
    this.scheduledDate,
    this.expectedParticipantsCount,
    this.participantsCompletedCount,
    this.participantFormStatus,
    this.channel,
    this.assignmentStatus,
    this.assignmentsTotal,
    this.assignmentsPending,
    this.assignmentBlockingReasons,
  });

  factory ReservationListItem.fromJson(Map<String, dynamic> json) {
    return ReservationListItem(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      code: json['code'] as String,
      status: (json['status'] as String).toReservationStatus(),
      participantCount: json['participant_count'] as int,
      paymentStatus: (json['payment_status'] as String).toPaymentStatus(),
      holderName: json['holder_name'] as String?,
      holderEmail: json['holder_email'] as String?,
      holderPhone: json['holder_phone'] as String?,
      assistantDisabled: json['assistant_disabled'] as bool?,
      experienceId: json['experience_id'] as String,
      experienceName: json['experience_name'] as String?,
      requestedDate: json['requested_date'] as String?,
      scheduledDate: json['scheduled_date'] as String?,
      expectedParticipantsCount: json['expected_participants_count'] as String?,
      participantsCompletedCount: json['participants_completed_count'] as int?,
      participantFormStatus: json['participant_form_status'] != null
          ? (json['participant_form_status'] as String)
                .toParticipantFormStatus()
          : null,
      channel: json['channel'] as String?,
      assignmentStatus: json['assignment_status'] as String?,
      assignmentsTotal: json['assignments_total'] as int?,
      assignmentsPending: json['assignments_pending'] as int?,
      assignmentBlockingReasons:
          (json['assignment_blocking_reasons'] as List<dynamic>?)
              ?.cast<String>(),
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'code': code,
    'status': status.toJson(),
    'participant_count': participantCount,
    'payment_status': paymentStatus.toJson(),
    'holder_name': holderName,
    'holder_email': holderEmail,
    'holder_phone': holderPhone,
    'assistant_disabled': assistantDisabled,
    'experience_id': experienceId,
    'experience_name': experienceName,
    'requested_date': requestedDate,
    'scheduled_date': scheduledDate,
    'expected_participants_count': expectedParticipantsCount,
    'participants_completed_count': participantsCompletedCount,
    'participant_form_status': participantFormStatus?.toJson(),
    'channel': channel,
    'assignment_status': assignmentStatus,
    'assignments_total': assignmentsTotal,
    'assignments_pending': assignmentsPending,
    'assignment_blocking_reasons': assignmentBlockingReasons,
  };
}
