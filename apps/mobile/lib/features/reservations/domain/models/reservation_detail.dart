import 'reservation_status.dart';
import 'reservation_payment_summary.dart';
import 'reservation_timeline_event.dart';
import 'reservation_operational_alert.dart';
import 'reservation_participant_detail.dart';
import 'reservation_payment_proof_detail.dart';

class ReservationDetail {
  const ReservationDetail({
    required this.id,
    required this.code,
    required this.status,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    this.experienceId,
    this.scheduleId,
    this.experienceName,
    this.scheduledDate,
    this.startTime,
    required this.participantCount,
    this.expectedParticipantsCount,
    required this.participantsCompletedCount,
    this.paymentStatus,
    this.participantFormStatus,
    this.formUrl,
    this.channel,
    this.quotedTotalAmount,
    this.currency,
    this.requestedDate,
    this.confirmedAt,
    this.cancelledAt,
    this.completedAt,
    this.deletedAt,
    this.paymentSummary,
    this.timeline = const [],
    this.operationalAlerts = const [],
    this.participants = const [],
    this.paymentProofs = const [],
  });

  final String id;
  final String code;
  final ReservationStatus status;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final String? experienceId;
  final String? scheduleId;
  final String? experienceName;
  final String? scheduledDate;
  final String? startTime;
  final int participantCount;
  final int? expectedParticipantsCount;
  final int participantsCompletedCount;
  final String? paymentStatus;
  final String? participantFormStatus;
  final String? formUrl;
  final String? channel;
  final String? quotedTotalAmount;
  final String? currency;
  final String? requestedDate;
  final String? confirmedAt;
  final String? cancelledAt;
  final String? completedAt;
  final DateTime? deletedAt;
  final ReservationPaymentSummary? paymentSummary;
  final List<ReservationTimelineEvent> timeline;
  final List<ReservationOperationalAlert> operationalAlerts;
  final List<ReservationParticipantDetail> participants;
  final List<ReservationPaymentProofDetail> paymentProofs;
}
