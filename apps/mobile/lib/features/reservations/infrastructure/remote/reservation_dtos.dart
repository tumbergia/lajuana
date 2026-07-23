class ReservationListItemDto {
  ReservationListItemDto({
    this.id,
    this.code,
    this.status,
    this.participantCount,
    this.paymentStatus,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    this.assistantDisabled = false,
    this.experienceId,
    this.experienceName,
    this.requestedDate,
    this.expectedParticipantsCount,
    this.participantsCompletedCount,
    this.participantFormStatus,
    this.channel,
    this.version,
    this.createdAt,
    this.updatedAt,
    this.deletedAt,
  });

  final String? id;
  final String? code;
  final String? status;
  final int? participantCount;
  final String? paymentStatus;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final bool assistantDisabled;
  final String? experienceId;
  final String? experienceName;
  final String? requestedDate;
  final int? expectedParticipantsCount;
  final int? participantsCompletedCount;
  final String? participantFormStatus;
  final String? channel;
  final int? version;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final DateTime? deletedAt;

  factory ReservationListItemDto.fromJson(Map<String, dynamic> json) {
    return ReservationListItemDto(
      id: json['id'] as String?,
      code: json['code'] as String?,
      status: json['status'] as String?,
      participantCount: json['participant_count'] as int?,
      paymentStatus: json['payment_status'] as String?,
      holderName: json['holder_name'] as String?,
      holderEmail: json['holder_email'] as String?,
      holderPhone: json['holder_phone'] as String?,
      assistantDisabled: json['assistant_disabled'] as bool? ?? false,
      experienceId: json['experience_id'] as String?,
      experienceName: json['experience_name'] as String?,
      requestedDate: json['requested_date'] as String?,
      expectedParticipantsCount: json['expected_participants_count'] as int?,
      participantsCompletedCount: json['participants_completed_count'] as int?,
      participantFormStatus: json['participant_form_status'] as String?,
      channel: json['channel'] as String?,
      version: json['version'] as int?,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String).toUtc(),
      updatedAt: json['updated_at'] == null
          ? null
          : DateTime.parse(json['updated_at'] as String).toUtc(),
      deletedAt: json['deleted_at'] == null
          ? null
          : DateTime.parse(json['deleted_at'] as String).toUtc(),
    );
  }
}

/// DTO for emergency contact nested inside participant.
class EmergencyContactDto {
  EmergencyContactDto({
    required this.name,
    required this.phone,
    this.relationship,
    this.country,
  });

  final String name;
  final String phone;
  final String? relationship;
  final String? country;

  factory EmergencyContactDto.fromJson(Map<String, dynamic> json) {
    return EmergencyContactDto(
      name: json['name'] as String? ?? '',
      phone: json['phone'] as String? ?? '',
      relationship: json['relationship'] as String?,
      country: json['country'] as String?,
    );
  }
}

/// DTO for a single participant within a reservation detail.
class ReservationParticipantDto {
  ReservationParticipantDto({
    required this.id,
    required this.reservationId,
    required this.firstName,
    required this.lastName,
    this.birthDate,
    this.documentType,
    this.documentNumber,
    this.phone,
    this.country,
    this.city,
    this.heightCm,
    this.weightKg,
    this.experienceLevel,
    this.dietaryRestrictions,
    this.bloodType,
    this.epsOrTravelInsurance,
    this.healthConditions,
    this.sensoryDisabilities,
    required this.emergencyContact,
    this.acceptedDataProcessing = false,
    this.acceptedMediaUsage,
    this.acceptedRiskRelease,
    this.isCompleted = false,
  });

  final String id;
  final String reservationId;
  final String firstName;
  final String lastName;
  final String? birthDate;
  final String? documentType;
  final String? documentNumber;
  final String? phone;
  final String? country;
  final String? city;
  final String? heightCm;
  final String? weightKg;
  final String? experienceLevel;
  final String? dietaryRestrictions;
  final String? bloodType;
  final String? epsOrTravelInsurance;
  final String? healthConditions;
  final String? sensoryDisabilities;
  final EmergencyContactDto emergencyContact;
  final bool acceptedDataProcessing;
  final bool? acceptedMediaUsage;
  final bool? acceptedRiskRelease;
  final bool isCompleted;

  String get fullName => '$firstName $lastName';

  factory ReservationParticipantDto.fromJson(Map<String, dynamic> json) {
    return ReservationParticipantDto(
      id: json['id'] as String? ?? '',
      reservationId: json['reservation_id'] as String? ?? '',
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      birthDate: json['birth_date'] as String?,
      documentType: json['document_type'] as String?,
      documentNumber: json['document_number'] as String?,
      phone: json['phone'] as String?,
      country: json['country'] as String?,
      city: json['city'] as String?,
      heightCm: json['height_cm']?.toString(),
      weightKg: json['weight_kg']?.toString(),
      experienceLevel: json['experience_level'] as String?,
      dietaryRestrictions: json['dietary_restrictions'] as String?,
      bloodType: json['blood_type'] as String?,
      epsOrTravelInsurance: json['eps_or_travel_insurance'] as String?,
      healthConditions: json['health_conditions'] as String?,
      sensoryDisabilities: json['sensory_disabilities'] as String?,
      emergencyContact: json['emergency_contact'] != null
          ? EmergencyContactDto.fromJson(
              json['emergency_contact'] as Map<String, dynamic>,
            )
          : EmergencyContactDto(name: '', phone: ''),
      acceptedDataProcessing:
          json['accepted_data_processing'] as bool? ?? false,
      acceptedMediaUsage: json['accepted_media_usage'] as bool?,
      acceptedRiskRelease: json['accepted_risk_release'] as bool?,
      isCompleted: json['is_completed'] as bool? ?? false,
    );
  }
}

/// DTO for a single payment proof within a reservation detail.
class ReservationPaymentProofDto {
  ReservationPaymentProofDto({
    required this.id,
    required this.reservationId,
    this.storageKey,
    this.filename,
    this.contentType,
    this.sizeBytes,
    this.sha256,
    this.status,
    this.uploadedAt,
  });

  final String id;
  final String reservationId;
  final String? storageKey;
  final String? filename;
  final String? contentType;
  final int? sizeBytes;
  final String? sha256;
  final String? status;
  final DateTime? uploadedAt;

  factory ReservationPaymentProofDto.fromJson(Map<String, dynamic> json) {
    return ReservationPaymentProofDto(
      id: json['id'] as String? ?? '',
      reservationId: json['reservation_id'] as String? ?? '',
      storageKey: json['storage_key'] as String?,
      filename: json['filename'] as String?,
      contentType: json['content_type'] as String?,
      sizeBytes: json['size_bytes'] as int?,
      sha256: json['sha256'] as String?,
      status: json['status'] as String?,
      uploadedAt: json['uploaded_at'] == null
          ? null
          : DateTime.parse(json['uploaded_at'] as String).toUtc(),
    );
  }
}

class ReservationDetailDto {
  ReservationDetailDto({
    this.id,
    this.code,
    this.experienceId,
    this.channel,
    this.status,
    this.participantCount,
    this.paymentStatus,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
    this.assistantDisabled = false,
    this.requestedDate,
    this.quotedTotalAmount,
    this.currency,
    this.expectedParticipantsCount,
    this.participantsCompletedCount,
    this.participantFormStatus,
    this.formUrl,
    this.confirmedAt,
    this.cancelledAt,
    this.completedAt,
    this.version,
    this.createdAt,
    this.updatedAt,
    this.deletedAt,
    this.participants = const [],
    this.paymentProofs = const [],
  });

  final String? id;
  final String? code;
  final String? experienceId;
  final String? channel;
  final String? status;
  final int? participantCount;
  final String? paymentStatus;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
  final bool assistantDisabled;
  final String? requestedDate;
  final String? quotedTotalAmount;
  final String? currency;
  final int? expectedParticipantsCount;
  final int? participantsCompletedCount;
  final String? participantFormStatus;
  final String? formUrl;
  final DateTime? confirmedAt;
  final DateTime? cancelledAt;
  final DateTime? completedAt;
  final int? version;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final DateTime? deletedAt;
  final List<ReservationParticipantDto> participants;
  final List<ReservationPaymentProofDto> paymentProofs;

  factory ReservationDetailDto.fromJson(Map<String, dynamic> json) {
    final rawParticipants = json['participants'] as List?;
    final rawProofs = json['payment_proofs'] as List?;

    return ReservationDetailDto(
      id: json['id'] as String?,
      code: json['code'] as String?,
      experienceId: json['experience_id'] as String?,
      channel: json['channel'] as String?,
      status: json['status'] as String?,
      participantCount: json['participant_count'] as int?,
      paymentStatus: json['payment_status'] as String?,
      holderName: json['holder_name'] as String?,
      holderEmail: json['holder_email'] as String?,
      holderPhone: json['holder_phone'] as String?,
      assistantDisabled: json['assistant_disabled'] as bool? ?? false,
      requestedDate: json['requested_date'] as String?,
      quotedTotalAmount: json['quoted_total_amount'] as String?,
      currency: json['currency'] as String?,
      expectedParticipantsCount: json['expected_participants_count'] as int?,
      participantsCompletedCount: json['participants_completed_count'] as int?,
      participantFormStatus: json['participant_form_status'] as String?,
      formUrl: json['form_url'] as String?,
      confirmedAt: json['confirmed_at'] == null
          ? null
          : DateTime.parse(json['confirmed_at'] as String).toUtc(),
      cancelledAt: json['cancelled_at'] == null
          ? null
          : DateTime.parse(json['cancelled_at'] as String).toUtc(),
      completedAt: json['completed_at'] == null
          ? null
          : DateTime.parse(json['completed_at'] as String).toUtc(),
      version: json['version'] as int?,
      createdAt: json['created_at'] == null
          ? null
          : DateTime.parse(json['created_at'] as String).toUtc(),
      updatedAt: json['updated_at'] == null
          ? null
          : DateTime.parse(json['updated_at'] as String).toUtc(),
      deletedAt: json['deleted_at'] == null
          ? null
          : DateTime.parse(json['deleted_at'] as String).toUtc(),
      participants: rawParticipants != null
          ? rawParticipants
                .map(
                  (e) => ReservationParticipantDto.fromJson(
                    e as Map<String, dynamic>,
                  ),
                )
                .toList(growable: false)
          : const [],
      paymentProofs: rawProofs != null
          ? rawProofs
                .map(
                  (e) => ReservationPaymentProofDto.fromJson(
                    e as Map<String, dynamic>,
                  ),
                )
                .toList(growable: false)
          : const [],
    );
  }
}

class ReservationTimelinePhotoDto {
  ReservationTimelinePhotoDto({
    required this.index,
    required this.storageKey,
    required this.filename,
    required this.contentType,
    this.sizeBytes = 0,
  });

  final int index;
  final String storageKey;
  final String filename;
  final String contentType;
  final int sizeBytes;

  factory ReservationTimelinePhotoDto.fromJson(Map<String, dynamic> json) {
    return ReservationTimelinePhotoDto(
      index: json['index'] as int? ?? 0,
      storageKey: json['storage_key'] as String? ?? '',
      filename: json['filename'] as String? ?? 'foto.jpg',
      contentType: json['content_type'] as String? ?? 'image/jpeg',
      sizeBytes: json['size_bytes'] as int? ?? 0,
    );
  }
}

class ReservationLogPhotoUploadDto {
  ReservationLogPhotoUploadDto({
    required this.storageKey,
    required this.filename,
    required this.contentType,
    this.sizeBytes = 0,
  });

  final String storageKey;
  final String filename;
  final String contentType;
  final int sizeBytes;

  factory ReservationLogPhotoUploadDto.fromJson(Map<String, dynamic> json) {
    return ReservationLogPhotoUploadDto(
      storageKey: json['storage_key'] as String? ?? '',
      filename: json['filename'] as String? ?? 'foto.jpg',
      contentType: json['content_type'] as String? ?? 'image/jpeg',
      sizeBytes: json['size_bytes'] as int? ?? 0,
    );
  }
}

class ReservationLogNoteDetailDto {
  ReservationLogNoteDetailDto({
    required this.id,
    required this.notes,
    this.photos = const [],
  });

  final String id;
  final String notes;
  final List<ReservationTimelinePhotoDto> photos;

  factory ReservationLogNoteDetailDto.fromJson(Map<String, dynamic> json) {
    final rawPhotos = json['photos'] as List?;
    return ReservationLogNoteDetailDto(
      id: json['id'] as String? ?? '',
      notes: json['notes'] as String? ?? '',
      photos: rawPhotos != null
          ? rawPhotos
                .map(
                  (item) => ReservationTimelinePhotoDto.fromJson(
                    Map<String, dynamic>.from(item as Map),
                  ),
                )
                .toList(growable: false)
          : const [],
    );
  }
}

class ReservationTimelineEntryDto {
  ReservationTimelineEntryDto({
    required this.id,
    required this.source,
    required this.kind,
    required this.happenedAt,
    required this.title,
    this.description,
    this.actorName,
    this.actorRole,
    this.editable = false,
    this.deletable = false,
    this.relatedParticipantId,
    this.serviceLogId,
    this.photos = const [],
    this.photosTotal = 0,
  });

  final String id;
  final String source;
  final String kind;
  final DateTime happenedAt;
  final String title;
  final String? description;
  final String? actorName;
  final String? actorRole;
  final bool editable;
  final bool deletable;
  final String? relatedParticipantId;
  final String? serviceLogId;
  final List<ReservationTimelinePhotoDto> photos;
  final int photosTotal;

  factory ReservationTimelineEntryDto.fromJson(Map<String, dynamic> json) {
    final rawPhotos = json['photos'] as List?;
    return ReservationTimelineEntryDto(
      id: json['id'] as String? ?? '',
      source: json['source'] as String? ?? '',
      kind: json['kind'] as String? ?? '',
      happenedAt: DateTime.parse(json['happened_at'] as String).toLocal(),
      title: json['title'] as String? ?? '',
      description: json['description'] as String?,
      actorName: json['actor_name'] as String?,
      actorRole: json['actor_role'] as String?,
      editable: json['editable'] as bool? ?? false,
      deletable: json['deletable'] as bool? ?? false,
      relatedParticipantId: json['related_participant_id'] as String?,
      serviceLogId: json['service_log_id'] as String?,
      photos: rawPhotos != null
          ? rawPhotos
                .map(
                  (item) => ReservationTimelinePhotoDto.fromJson(
                    Map<String, dynamic>.from(item as Map),
                  ),
                )
                .toList(growable: false)
          : const [],
      photosTotal: json['photos_total'] as int? ?? 0,
    );
  }
}

class ReservationProviderItemDto {
  ReservationProviderItemDto({
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
  final String? scheduledDate;
  final int participantsCount;

  factory ReservationProviderItemDto.fromJson(Map<String, dynamic> json) {
    return ReservationProviderItemDto(
      reservationProviderId: json['reservation_provider_id'] as String? ?? '',
      reservationId: json['reservation_id'] as String? ?? '',
      providerId: json['provider_id'] as String? ?? '',
      providerName: json['provider_name'] as String? ?? '',
      providerType: json['provider_type'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      serviceLabel: json['service_label'] as String?,
      contactName: json['contact_name'] as String?,
      email: json['email'] as String?,
      whatsappPhone: json['whatsapp_phone'] as String?,
      locationLabel: json['location_label'] as String?,
      capacityNotes: json['capacity_notes'] as String?,
      operationalNotes: json['operational_notes'] as String?,
      tariffNotes: json['tariff_notes'] as String?,
      notes: json['notes'] as String?,
      reservationCode: json['reservation_code'] as String? ?? '',
      experienceName: json['experience_name'] as String?,
      scheduledDate: json['scheduled_date'] as String?,
      participantsCount: json['participants_count'] as int? ?? 0,
    );
  }
}

class ProviderCatalogItemDto {
  ProviderCatalogItemDto({
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

  factory ProviderCatalogItemDto.fromJson(Map<String, dynamic> json) {
    return ProviderCatalogItemDto(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      slug: json['slug'] as String? ?? '',
      type: json['type'] as String? ?? '',
      status: json['status'] as String? ?? 'active',
      isActive: json['is_active'] as bool? ?? true,
      locationLabel: json['location_label'] as String?,
    );
  }
}
