import 'reservation_status.dart';

class ReservationListItem {
  const ReservationListItem({
    required this.id,
    required this.code,
    required this.status,
    this.experienceName,
    this.experienceId,
    this.scheduledDate,
    this.startTime,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    required this.participantCount,
    this.registeredParticipantsCount,
    this.paymentStatus,
    this.participantFormStatus,
    this.originChannel,
    this.scheduleId,
    required this.hasOperationalAlerts,
    this.requestedDate,
    this.createdAt,
    this.updatedAt,
    this.deletedAt,
  });

  final String id;
  final String code;
  final ReservationStatus status;
  final String? experienceName;
  final String? experienceId;
  final String? scheduledDate;
  final String? startTime;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final int participantCount;
  final int? registeredParticipantsCount;
  final String? paymentStatus;
  final String? participantFormStatus;
  final String? originChannel;
  final String? scheduleId;
  final bool hasOperationalAlerts;
  final String? requestedDate;
  final String? createdAt;
  final String? updatedAt;
  final DateTime? deletedAt;

  bool get isDeleted => deletedAt != null;
}
