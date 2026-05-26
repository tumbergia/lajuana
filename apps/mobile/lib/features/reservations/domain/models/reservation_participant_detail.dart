/// Full participant detail within a reservation.
/// This is NOT a minimal summary — it carries operational fields
/// needed by the participants section and blocker computation.
class ReservationParticipantDetail {
  const ReservationParticipantDetail({
    required this.id,
    required this.reservationId,
    required this.fullName,
    this.firstName,
    this.lastName,
    this.birthDate,
    this.ageYears,
    this.heightCm,
    this.weightKg,
    this.experienceLevel,
    this.documentType,
    this.documentNumber,
    this.phone,
    this.country,
    this.city,
    this.bloodType,
    this.epsOrTravelInsurance,
    this.dietaryRestrictions,
    this.healthConditions,
    this.sensoryDisabilities,
    this.emergencyContactName,
    this.emergencyContactPhone,
    this.emergencyContactRelationship,
    this.acceptedDataProcessing = false,
    this.acceptedMediaUsage,
    this.acceptedRiskRelease,
    this.isCompleted = false,
  });

  final String id;
  final String reservationId;
  final String fullName;
  final String? firstName;
  final String? lastName;
  final String? birthDate;
  final int? ageYears;
  final String? heightCm;
  final String? weightKg;
  final String? experienceLevel;
  final String? documentType;
  final String? documentNumber;
  final String? phone;
  final String? country;
  final String? city;
  final String? bloodType;
  final String? epsOrTravelInsurance;
  final String? dietaryRestrictions;
  final String? healthConditions;
  final String? sensoryDisabilities;
  final String? emergencyContactName;
  final String? emergencyContactPhone;
  final String? emergencyContactRelationship;
  final bool acceptedDataProcessing;
  final bool? acceptedMediaUsage;
  final bool? acceptedRiskRelease;
  final bool isCompleted;

  /// True when the participant has a medical condition or disability alert.
  bool get hasMedicalAlert =>
      (healthConditions != null && healthConditions!.trim().isNotEmpty) ||
      (sensoryDisabilities != null && sensoryDisabilities!.trim().isNotEmpty);

  /// True when the participant has a food restriction.
  bool get hasFoodRestriction =>
      dietaryRestrictions != null && dietaryRestrictions!.trim().isNotEmpty;

  /// True when the participant has consented to photo/video usage.
  bool? get photoVideoConsent => acceptedMediaUsage;

  /// True when required operational fields are missing.
  bool get hasMissingRequiredFields =>
      !isCompleted ||
      heightCm == null ||
      weightKg == null ||
      experienceLevel == null;
}
