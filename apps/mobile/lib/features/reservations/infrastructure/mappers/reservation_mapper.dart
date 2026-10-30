import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_domain/src/reservations/reservation_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservation_participant_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_proof_detail.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_summary.dart';
import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_entry.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_photo.dart';
import 'package:mobile_domain/src/reservations/reservation_timeline_event.dart';
import 'package:mobile/features/reservations/presentation/models/reservation_view_models.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservation_dtos.dart';

/// Maps a DTO participant to a domain participant detail.
ReservationParticipantDetail _participantDtoToDetail(
  ReservationParticipantDto dto,
) {
  // Rough age computation from birth_date string.
  int? ageYears;
  if (dto.birthDate != null && dto.birthDate!.length >= 10) {
    try {
      final year = int.tryParse(dto.birthDate!.substring(0, 4));
      if (year != null) {
        ageYears = DateTime.now().year - year;
      }
    } catch (_) {}
  }

  return ReservationParticipantDetail(
    id: dto.id,
    reservationId: dto.reservationId,
    fullName: dto.fullName,
    firstName: dto.firstName,
    lastName: dto.lastName,
    birthDate: dto.birthDate,
    ageYears: ageYears,
    heightCm: dto.heightCm,
    weightKg: dto.weightKg,
    experienceLevel: dto.experienceLevel,
    documentType: dto.documentType,
    documentNumber: dto.documentNumber,
    phone: dto.phone,
    country: dto.country,
    city: dto.city,
    bloodType: dto.bloodType,
    epsOrTravelInsurance: dto.epsOrTravelInsurance,
    dietaryRestrictions: dto.dietaryRestrictions,
    healthConditions: dto.healthConditions,
    sensoryDisabilities: dto.sensoryDisabilities,
    emergencyContactName: dto.emergencyContact.name,
    emergencyContactPhone: dto.emergencyContact.phone,
    emergencyContactRelationship: dto.emergencyContact.relationship,
    acceptedDataProcessing: dto.acceptedDataProcessing,
    acceptedMediaUsage: dto.acceptedMediaUsage,
    acceptedRiskRelease: dto.acceptedRiskRelease,
    isCompleted: dto.isCompleted,
  );
}

/// Maps a DTO payment proof to a domain payment proof detail.
ReservationPaymentProofDetail _paymentProofDtoToDetail(
  ReservationPaymentProofDto dto,
) {
  return ReservationPaymentProofDetail(
    id: dto.id,
    reservationId: dto.reservationId,
    filename: dto.filename,
    contentType: dto.contentType,
    sizeBytes: dto.sizeBytes,
    status: dto.status,
    uploadedAt: dto.uploadedAt,
    storageKey: dto.storageKey,
    sha256: dto.sha256,
  );
}

/// Statuses that should appear as "pendiente" in the UI filter group.
bool _isPendingGroup(ReservationStatus status) {
  switch (status) {
    case ReservationStatus.contact:
    case ReservationStatus.quoted:
    case ReservationStatus.preReserved:
    case ReservationStatus.pendingPayment:
    case ReservationStatus.paymentReceived:
      return true;
    case ReservationStatus.confirmed:
    case ReservationStatus.cancelled:
    case ReservationStatus.completed:
    case ReservationStatus.expired:
    case ReservationStatus.unknown:
      return false;
  }
}

/// Statuses that should appear as "confirmadas" in the UI filter group.
bool _isConfirmedGroup(ReservationStatus status) {
  return status == ReservationStatus.confirmed;
}

/// Maps a backend status string to a UI filter group label.
String reservationStatusToFilterGroup(ReservationStatus status) {
  if (_isPendingGroup(status)) return 'pendientes';
  if (_isConfirmedGroup(status)) return 'confirmadas';
  return 'cerradas';
}

/// Maps a backend status string to an AppBadgeTone.
AppBadgeTone reservationStatusToBadgeTone(ReservationStatus status) {
  switch (status) {
    case ReservationStatus.contact:
    case ReservationStatus.quoted:
    case ReservationStatus.preReserved:
      return AppBadgeTone.neutral;
    case ReservationStatus.pendingPayment:
    case ReservationStatus.paymentReceived:
      return AppBadgeTone.warning;
    case ReservationStatus.confirmed:
      return AppBadgeTone.primary;
    case ReservationStatus.cancelled:
      return AppBadgeTone.danger;
    case ReservationStatus.completed:
      return AppBadgeTone.success;
    case ReservationStatus.expired:
      return AppBadgeTone.danger;
    case ReservationStatus.unknown:
      return AppBadgeTone.neutral;
  }
}

/// Maps a backend payment status string to an AppBadgeTone.
AppBadgeTone paymentStatusToBadgeTone(String? paymentStatus) {
  switch (paymentStatus?.toLowerCase()) {
    case 'pending':
      return AppBadgeTone.warning;
    case 'received':
      return AppBadgeTone.primary;
    case 'verified':
      return AppBadgeTone.success;
    case 'rejected':
      return AppBadgeTone.danger;
    default:
      return AppBadgeTone.neutral;
  }
}

/// Derives a timeline from reservation state fields when no real timeline exists.
List<ReservationTimelineEvent> deriveFallbackTimeline(
  ReservationDetail detail,
) {
  final events = <ReservationTimelineEvent>[];

  if (detail.requestedDate != null) {
    events.add(
      ReservationTimelineEvent(
        date: detail.requestedDate,
        title: 'Fecha solicitada',
        type: 'completed',
      ),
    );
  }

  if (detail.paymentStatus == 'verified' ||
      detail.paymentStatus == 'received') {
    events.add(
      ReservationTimelineEvent(
        title: 'Pago registrado',
        description: 'Estado: ${detail.paymentStatus}',
        type: 'completed',
      ),
    );
  }

  if (detail.status == ReservationStatus.confirmed &&
      detail.confirmedAt != null) {
    events.add(
      ReservationTimelineEvent(
        date: detail.confirmedAt,
        title: 'Reserva confirmada',
        type: 'active',
      ),
    );
  }

  if (detail.status == ReservationStatus.completed &&
      detail.completedAt != null) {
    events.add(
      ReservationTimelineEvent(
        date: detail.completedAt,
        title: 'Reserva completada',
        type: 'completed',
      ),
    );
  }

  return events;
}

/// DTO -> Domain: ReservationListItemDto -> ReservationListItem
ReservationListItem dtoToListItem(ReservationListItemDto dto) {
  return ReservationListItem(
    id: dto.id ?? '',
    code: dto.code ?? '',
    status: parseReservationStatus(dto.status),
    experienceId: dto.experienceId,
    experienceName: dto.experienceName,
    holderName: dto.holderName,
    holderEmail: dto.holderEmail,
    holderPhone: dto.holderPhone,
    assistantDisabled: dto.assistantDisabled,
    participantCount: dto.participantCount ?? 0,
    registeredParticipantsCount: dto.participantsCompletedCount,
    paymentStatus: dto.paymentStatus,
    participantFormStatus: dto.participantFormStatus,
    originChannel: dto.channel,
    hasOperationalAlerts: false,
    requestedDate: dto.requestedDate,
    createdAt: dto.createdAt?.toIso8601String(),
    updatedAt: dto.updatedAt?.toIso8601String(),
    deletedAt: dto.deletedAt,
  );
}

/// DTO -> Domain: ReservationDetailDto -> ReservationDetail
ReservationDetail dtoToDetail(ReservationDetailDto dto) {
  // Build basic detail first
  final baseDetail = ReservationDetail(
    id: dto.id ?? '',
    code: dto.code ?? '',
    status: parseReservationStatus(dto.status),
    holderName: dto.holderName,
    holderEmail: dto.holderEmail,
    holderPhone: dto.holderPhone,
    assistantDisabled: dto.assistantDisabled,
    experienceId: dto.experienceId,
    participantCount: dto.participantCount ?? 0,
    expectedParticipantsCount: dto.expectedParticipantsCount,
    participantsCompletedCount: dto.participantsCompletedCount ?? 0,
    paymentStatus: dto.paymentStatus,
    participantFormStatus: dto.participantFormStatus,
    formUrl: dto.formUrl,
    channel: dto.channel,
    quotedTotalAmount: dto.quotedTotalAmount,
    currency: dto.currency,
    requestedDate: dto.requestedDate,
    confirmedAt: dto.confirmedAt?.toIso8601String(),
    cancelledAt: dto.cancelledAt?.toIso8601String(),
    completedAt: dto.completedAt?.toIso8601String(),
    deletedAt: dto.deletedAt,
    paymentSummary: ReservationPaymentSummary(
      status: dto.paymentStatus,
      proofCount: dto.paymentProofs.length,
    ),
    timeline: const [],
    operationalAlerts: const [],
  );

  return ReservationDetail(
    id: baseDetail.id,
    code: baseDetail.code,
    status: baseDetail.status,
    holderName: baseDetail.holderName,
    holderEmail: baseDetail.holderEmail,
    holderPhone: baseDetail.holderPhone,
    assistantDisabled: baseDetail.assistantDisabled,
    experienceId: baseDetail.experienceId,
    participantCount: baseDetail.participantCount,
    expectedParticipantsCount: baseDetail.expectedParticipantsCount,
    participantsCompletedCount: baseDetail.participantsCompletedCount,
    paymentStatus: baseDetail.paymentStatus,
    participantFormStatus: baseDetail.participantFormStatus,
    formUrl: baseDetail.formUrl,
    channel: baseDetail.channel,
    quotedTotalAmount: baseDetail.quotedTotalAmount,
    currency: baseDetail.currency,
    requestedDate: baseDetail.requestedDate,
    confirmedAt: baseDetail.confirmedAt,
    cancelledAt: baseDetail.cancelledAt,
    completedAt: baseDetail.completedAt,
    deletedAt: baseDetail.deletedAt,
    paymentSummary: baseDetail.paymentSummary,
    timeline: deriveFallbackTimeline(baseDetail),
    operationalAlerts: baseDetail.operationalAlerts,
    participants: dto.participants
        .map(_participantDtoToDetail)
        .toList(growable: false),
    paymentProofs: dto.paymentProofs
        .map(_paymentProofDtoToDetail)
        .toList(growable: false),
  );
}

/// Domain -> ViewModel: ReservationListItem -> ReservationRecord
ReservationRecord listItemToRecord(
  ReservationListItem item, {
  String slotLabel = '',
}) {
  final filterGroup = reservationStatusToFilterGroup(item.status);
  final effectiveSlotLabel = slotLabel.isNotEmpty
      ? slotLabel
      : (item.requestedDate ?? '');
  return ReservationRecord(
    id: item.id,
    code: item.code,
    clientName: item.holderName ?? item.holderEmail ?? 'Sin titular',
    equineName: item.experienceName ?? '',
    slotLabel: effectiveSlotLabel,
    status: filterGroup,
    statusRaw: item.status,
    experienceName: item.experienceName,
    participantCount: item.participantCount,
    registeredCount: item.registeredParticipantsCount,
    paymentStatus: item.paymentStatus,
    formStatus: item.participantFormStatus,
    requestedDate: item.requestedDate,
    hasPendingSync: false,
    hasSyncError: false,
    isDeleted: item.isDeleted,
  );
}

ReservationTimelineEntry timelineEntryDtoToDomain(
  ReservationTimelineEntryDto dto,
) {
  return ReservationTimelineEntry(
    id: dto.id,
    source: dto.source,
    kind: dto.kind,
    happenedAt: dto.happenedAt,
    title: dto.title,
    description: dto.description,
    actorName: dto.actorName,
    actorRole: dto.actorRole,
    editable: dto.editable,
    deletable: dto.deletable,
    relatedParticipantId: dto.relatedParticipantId,
    serviceLogId: dto.serviceLogId,
    photos: dto.photos
        .map(
          (photo) => ReservationTimelinePhoto(
            index: photo.index,
            storageKey: photo.storageKey,
            filename: photo.filename,
            contentType: photo.contentType,
            sizeBytes: photo.sizeBytes,
          ),
        )
        .toList(growable: false),
    photosTotal: dto.photosTotal > 0 ? dto.photosTotal : dto.photos.length,
  );
}

String timelineEntryNodeType(ReservationTimelineEntry entry) {
  if (entry.kind.contains('rejected') || entry.kind == 'incident') {
    return 'error';
  }
  if (entry.kind == 'note') {
    return 'active';
  }
  if (entry.kind == 'reservation.confirmed' ||
      entry.kind == 'payment_proof.approved' ||
      entry.kind == 'arrival' ||
      entry.kind == 'closure' ||
      entry.kind == 'participant.registered') {
    return 'completed';
  }
  return 'neutral';
}

String formatTimelineDate(DateTime dateTime) {
  final local = dateTime.toLocal();
  final day = local.day.toString().padLeft(2, '0');
  const months = [
    'ENE',
    'FEB',
    'MAR',
    'ABR',
    'MAY',
    'JUN',
    'JUL',
    'AGO',
    'SEP',
    'OCT',
    'NOV',
    'DIC',
  ];
  final month = months[local.month - 1];
  final year = local.year;
  final hour = local.hour.toString().padLeft(2, '0');
  final minute = local.minute.toString().padLeft(2, '0');
  return '$day $month $year · $hour:$minute';
}

ReservationProviderItem reservationProviderDtoToDomain(
  ReservationProviderItemDto dto,
) {
  DateTime? scheduledDate;
  if (dto.scheduledDate != null && dto.scheduledDate!.isNotEmpty) {
    scheduledDate = DateTime.tryParse(dto.scheduledDate!);
  }
  return ReservationProviderItem(
    reservationProviderId: dto.reservationProviderId,
    reservationId: dto.reservationId,
    providerId: dto.providerId,
    providerName: dto.providerName,
    providerType: dto.providerType,
    status: dto.status,
    serviceLabel: dto.serviceLabel,
    contactName: dto.contactName,
    email: dto.email,
    whatsappPhone: dto.whatsappPhone,
    locationLabel: dto.locationLabel,
    capacityNotes: dto.capacityNotes,
    operationalNotes: dto.operationalNotes,
    tariffNotes: dto.tariffNotes,
    notes: dto.notes,
    reservationCode: dto.reservationCode,
    experienceName: dto.experienceName,
    scheduledDate: scheduledDate,
    participantsCount: dto.participantsCount,
  );
}

ProviderCatalogItem providerCatalogDtoToDomain(ProviderCatalogItemDto dto) {
  return ProviderCatalogItem(
    id: dto.id,
    name: dto.name,
    slug: dto.slug,
    type: dto.type,
    status: dto.status,
    isActive: dto.isActive,
    locationLabel: dto.locationLabel,
  );
}
