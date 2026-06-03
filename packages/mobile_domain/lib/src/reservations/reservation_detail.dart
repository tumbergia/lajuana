import '../reservation_status.dart';
import '../gen/reservation.dart' as gen;
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

  /// Crea un [ReservationDetail] de dominio desde el modelo generado [gen.Reservation].
  ///
  /// Mapea toda la jerarquía: participantes y comprobantes se convierten vía sus
  /// respectivos factories. Los agregados que no existen en el modelo generado
  /// (paymentSummary, timeline, operationalAlerts) se inicializan vacíos.
  factory ReservationDetail.fromGen(gen.Reservation source) {
    return ReservationDetail(
      id: source.id,
      code: source.code,
      status: parseReservationStatus(source.status.value),
      holderName: source.holderName.isNotEmpty ? source.holderName : null,
      holderEmail: source.holderEmail.isNotEmpty ? source.holderEmail : null,
      holderPhone: source.holderPhone.isNotEmpty ? source.holderPhone : null,
      experienceId: source.experienceId,
      scheduleId: source.scheduleId,
      experienceName: null,
      scheduledDate: null,
      startTime: null,
      participantCount: source.participantCount,
      expectedParticipantsCount: int.tryParse(source.expectedParticipantsCount),
      participantsCompletedCount: source.participantsCompletedCount,
      paymentStatus: source.paymentStatus.value,
      participantFormStatus: source.participantFormStatus.value,
      formUrl: source.formUrl.isNotEmpty ? source.formUrl : null,
      channel: source.channel.value,
      quotedTotalAmount:
          source.quotedTotalAmount.isNotEmpty ? source.quotedTotalAmount : null,
      currency: source.currency.isNotEmpty ? source.currency : null,
      requestedDate: source.requestedDate.isNotEmpty ? source.requestedDate : null,
      confirmedAt: source.confirmedAt.isNotEmpty ? source.confirmedAt : null,
      cancelledAt: source.cancelledAt.isNotEmpty ? source.cancelledAt : null,
      completedAt: source.completedAt.isNotEmpty ? source.completedAt : null,
      deletedAt: source.deletedAt != null
          ? DateTime.tryParse(source.deletedAt!)
          : null,
      paymentSummary: null,
      timeline: const [],
      operationalAlerts: const [],
      participants: source.participants
              ?.map((p) => ReservationParticipantDetail.fromGen(p))
              .toList() ??
          [],
      paymentProofs: source.paymentProofs
              ?.map((p) => ReservationPaymentProofDetail.fromGen(p))
              .toList() ??
          [],
    );
  }

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
