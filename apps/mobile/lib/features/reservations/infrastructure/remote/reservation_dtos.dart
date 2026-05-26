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
    this.experienceId,
    this.experienceName,
    this.scheduleId,
    this.requestedDate,
    this.scheduledDate,
    this.startTime,
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
  final String? experienceId;
  final String? experienceName;
  final String? scheduleId;
  final String? requestedDate;
  final String? scheduledDate;
  final String? startTime;
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
      experienceId: json['experience_id'] as String?,
      experienceName: json['experience_name'] as String?,
      scheduleId: json['schedule_id'] as String?,
      requestedDate: json['requested_date'] as String?,
      scheduledDate: json['scheduled_date'] as String?,
      startTime: json['start_time'] as String?,
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
              json['emergency_contact'] as Map<String, dynamic>)
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
    this.scheduleId,
    this.channel,
    this.status,
    this.participantCount,
    this.paymentStatus,
    this.holderName,
    this.holderEmail,
    this.holderPhone,
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
  final String? scheduleId;
  final String? channel;
  final String? status;
  final int? participantCount;
  final String? paymentStatus;
  final String? holderName;
  final String? holderEmail;
  final String? holderPhone;
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
      scheduleId: json['schedule_id'] as String?,
      channel: json['channel'] as String?,
      status: json['status'] as String?,
      participantCount: json['participant_count'] as int?,
      paymentStatus: json['payment_status'] as String?,
      holderName: json['holder_name'] as String?,
      holderEmail: json['holder_email'] as String?,
      holderPhone: json['holder_phone'] as String?,
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
              .map((e) => ReservationParticipantDto.fromJson(
                  e as Map<String, dynamic>))
              .toList(growable: false)
          : const [],
      paymentProofs: rawProofs != null
          ? rawProofs
              .map((e) => ReservationPaymentProofDto.fromJson(
                  e as Map<String, dynamic>))
              .toList(growable: false)
          : const [],
    );
  }
}
