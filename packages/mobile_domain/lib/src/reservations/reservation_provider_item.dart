class ReservationProviderItem {
  const ReservationProviderItem({
    required this.reservationProviderId,
    required this.reservationId,
    required this.providerId,
    required this.providerName,
    required this.providerType,
    required this.status,
    this.serviceLabel,
    this.contactName,
    this.email,
    this.whatsappPhone,
    this.locationLabel,
    this.capacityNotes,
    this.operationalNotes,
    this.tariffNotes,
    this.notes,
    required this.reservationCode,
    this.experienceName,
    this.scheduledDate,
    required this.participantsCount,
  });

  final String reservationProviderId;
  final String reservationId;
  final String providerId;
  final String providerName;
  final String providerType;
  final String status;
  final String? serviceLabel;
  final String? contactName;
  final String? email;
  final String? whatsappPhone;
  final String? locationLabel;
  final String? capacityNotes;
  final String? operationalNotes;
  final String? tariffNotes;
  final String? notes;
  final String reservationCode;
  final String? experienceName;
  final DateTime? scheduledDate;
  final int participantsCount;
}

class ProviderCatalogItem {
  const ProviderCatalogItem({
    required this.id,
    required this.name,
    required this.slug,
    required this.type,
    required this.status,
    required this.isActive,
    this.locationLabel,
  });

  final String id;
  final String name;
  final String slug;
  final String type;
  final String status;
  final bool isActive;
  final String? locationLabel;
}
