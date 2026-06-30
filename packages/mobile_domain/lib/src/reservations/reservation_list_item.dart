import '../reservation_status.dart';
import '../gen/reservation_list_item.dart' as gen;

class ReservationListItem {
  const ReservationListItem({
    required this.id,
    required this.code,
    required this.status,
    this.experienceName,
    this.experienceId,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    required this.participantCount,
    this.registeredParticipantsCount,
    this.paymentStatus,
    this.participantFormStatus,
    this.originChannel,
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
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final int participantCount;
  final int? registeredParticipantsCount;
  final String? paymentStatus;
  final String? participantFormStatus;
  final String? originChannel;
  final bool hasOperationalAlerts;
  final String? requestedDate;
  final String? createdAt;
  final String? updatedAt;
  final DateTime? deletedAt;

  bool get isDeleted => deletedAt != null;

  /// Crea un [ReservationListItem] de dominio desde el modelo generado.
  factory ReservationListItem.fromGen(gen.ReservationListItem source) {
    return ReservationListItem(
      id: source.id,
      code: source.code,
      status: parseReservationStatus(source.status.value),
      experienceName: source.experienceName,
      experienceId: source.experienceId,
      holderName: source.holderName,
      holderEmail: source.holderEmail,
      holderPhone: source.holderPhone,
      participantCount: source.participantCount,
      registeredParticipantsCount: source.participantsCompletedCount,
      paymentStatus: source.paymentStatus.value,
      participantFormStatus: source.participantFormStatus?.value,
      originChannel: source.channel,
      hasOperationalAlerts: false,
      requestedDate: source.requestedDate,
      createdAt: null,
      updatedAt: null,
      deletedAt: source.deletedAt != null
          ? DateTime.tryParse(source.deletedAt!)
          : null,
    );
  }
}
