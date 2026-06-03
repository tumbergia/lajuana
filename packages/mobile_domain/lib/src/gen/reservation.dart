// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ReservationResponseSchema`.

import 'channel.dart';
import 'participant.dart';
import 'participant_form_status.dart';
import 'payment_proof.dart';
import 'payment_status.dart';
import 'reservation_status.dart';

class Reservation {

  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String code;
  final String experienceId;
  final String scheduleId;
  final Channel channel;
  final ReservationStatus status;
  final int participantCount;
  final PaymentStatus paymentStatus;
  final String holderName;
  final String holderEmail;
  final String holderPhone;
  final String requestedDate;
  final String quotedTotalAmount;
  final String currency;
  final String expectedParticipantsCount;
  final int participantsCompletedCount;
  final ParticipantFormStatus participantFormStatus;
  final String formUrl;
  final String? participantFormSentAt;
  final int? participantFormSendCount;
  final bool? formSent;
  final String? confirmationMessageSentAt;
  final bool? confirmationMessageSent;
  final String confirmedAt;
  final String cancelledAt;
  final String completedAt;
  final List<Participant>? participants;
  final List<PaymentProof>? paymentProofs;
  final String? assignmentStatus;
  final int? assignmentsTotal;
  final int? assignmentsPending;
  final List<String>? assignmentBlockingReasons;

  const Reservation(
    {
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.code,
    required this.experienceId,
    required this.scheduleId,
    required this.channel,
    required this.status,
    required this.participantCount,
    required this.paymentStatus,
    required this.holderName,
    required this.holderEmail,
    required this.holderPhone,
    required this.requestedDate,
    required this.quotedTotalAmount,
    required this.currency,
    required this.expectedParticipantsCount,
    required this.participantsCompletedCount,
    required this.participantFormStatus,
    required this.formUrl,
    this.participantFormSentAt,
    this.participantFormSendCount,
    this.formSent,
    this.confirmationMessageSentAt,
    this.confirmationMessageSent,
    required this.confirmedAt,
    required this.cancelledAt,
    required this.completedAt,
    this.participants,
    this.paymentProofs,
    this.assignmentStatus,
    this.assignmentsTotal,
    this.assignmentsPending,
    this.assignmentBlockingReasons,
    }
  );

  factory Reservation.fromJson(Map<String, dynamic> json) {
    return Reservation(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      code: json['code'] as String,
      experienceId: json['experience_id'] as String,
      scheduleId: json['schedule_id'] as String,
      channel: (json['channel'] as String).toChannel(),
      status: (json['status'] as String).toReservationStatus(),
      participantCount: json['participant_count'] as int,
      paymentStatus: (json['payment_status'] as String).toPaymentStatus(),
      holderName: json['holder_name'] as String,
      holderEmail: json['holder_email'] as String,
      holderPhone: json['holder_phone'] as String,
      requestedDate: json['requested_date'] as String,
      quotedTotalAmount: json['quoted_total_amount'] as String,
      currency: json['currency'] as String,
      expectedParticipantsCount: json['expected_participants_count'] as String,
      participantsCompletedCount: json['participants_completed_count'] as int,
      participantFormStatus: (json['participant_form_status'] as String).toParticipantFormStatus(),
      formUrl: json['form_url'] as String,
      participantFormSentAt: json['participant_form_sent_at'] as String?,
      participantFormSendCount: json['participant_form_send_count'] as int?,
      formSent: json['form_sent'] as bool?,
      confirmationMessageSentAt: json['confirmation_message_sent_at'] as String?,
      confirmationMessageSent: json['confirmation_message_sent'] as bool?,
      confirmedAt: json['confirmed_at'] as String,
      cancelledAt: json['cancelled_at'] as String,
      completedAt: json['completed_at'] as String,
      participants: (json['participants'] as List<dynamic>?)
        ?.map((e) => Participant.fromJson(e as Map<String, dynamic>)).toList(),
      paymentProofs: (json['payment_proofs'] as List<dynamic>?)
        ?.map((e) => PaymentProof.fromJson(e as Map<String, dynamic>)).toList(),
      assignmentStatus: json['assignment_status'] as String?,
      assignmentsTotal: json['assignments_total'] as int?,
      assignmentsPending: json['assignments_pending'] as int?,
      assignmentBlockingReasons: (json['assignment_blocking_reasons'] as List<dynamic>?)
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
    'experience_id': experienceId,
    'schedule_id': scheduleId,
    'channel': channel.toJson(),
    'status': status.toJson(),
    'participant_count': participantCount,
    'payment_status': paymentStatus.toJson(),
    'holder_name': holderName,
    'holder_email': holderEmail,
    'holder_phone': holderPhone,
    'requested_date': requestedDate,
    'quoted_total_amount': quotedTotalAmount,
    'currency': currency,
    'expected_participants_count': expectedParticipantsCount,
    'participants_completed_count': participantsCompletedCount,
    'participant_form_status': participantFormStatus.toJson(),
    'form_url': formUrl,
    'participant_form_sent_at': participantFormSentAt,
    'participant_form_send_count': participantFormSendCount,
    'form_sent': formSent,
    'confirmation_message_sent_at': confirmationMessageSentAt,
    'confirmation_message_sent': confirmationMessageSent,
    'confirmed_at': confirmedAt,
    'cancelled_at': cancelledAt,
    'completed_at': completedAt,
    'participants': participants,
    'payment_proofs': paymentProofs,
    'assignment_status': assignmentStatus,
    'assignments_total': assignmentsTotal,
    'assignments_pending': assignmentsPending,
    'assignment_blocking_reasons': assignmentBlockingReasons,
  };

}
