import 'reservation_status.dart';
import 'reservation_payment_summary.dart';
import 'reservation_timeline_event.dart';
import 'reservation_operational_alert.dart';

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
    this.paymentSummary,
    this.timeline = const [],
    this.operationalAlerts = const [],
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
  final ReservationPaymentSummary? paymentSummary;
  final List<ReservationTimelineEvent> timeline;
  final List<ReservationOperationalAlert> operationalAlerts;
}
