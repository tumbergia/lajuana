import 'dart:convert';

import '../gen/participant.dart' as gen;

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

  /// Crea un [ReservationParticipantDetail] de dominio desde el modelo generado.
  factory ReservationParticipantDetail.fromGen(gen.Participant source) {
    // Parse emergency_contact string → JSON object if possible.
    String? ecName;
    String? ecPhone;
    String? ecRelation;
    if (source.emergencyContact != null && source.emergencyContact!.isNotEmpty) {
      try {
        final ec = jsonDecode(source.emergencyContact!);
        if (ec is Map<String, dynamic>) {
          ecName = ec['name'] as String?;
          ecPhone = ec['phone'] as String?;
          ecRelation = ec['relationship'] as String?;
        }
      } catch (_) {
        // Not JSON, treat as raw string → name
        ecName = source.emergencyContact;
      }
    }

    return ReservationParticipantDetail(
      id: source.id,
      reservationId: source.reservationId,
      fullName: '${source.firstName} ${source.lastName}',
      firstName: source.firstName,
      lastName: source.lastName,
      birthDate: source.birthDate.toIso8601String(),
      heightCm: source.heightCm.isNotEmpty ? source.heightCm : null,
      weightKg: source.weightKg.isNotEmpty ? source.weightKg : null,
      experienceLevel: source.experienceLevel,
      documentType: source.documentType.isNotEmpty ? source.documentType : null,
      documentNumber: source.documentNumber.isNotEmpty ? source.documentNumber : null,
      phone: source.phone.isNotEmpty ? source.phone : null,
      country: source.country.isNotEmpty ? source.country : null,
      city: source.city.isNotEmpty ? source.city : null,
      bloodType: source.bloodType.isNotEmpty ? source.bloodType : null,
      epsOrTravelInsurance:
          source.epsOrTravelInsurance.isNotEmpty ? source.epsOrTravelInsurance : null,
      dietaryRestrictions:
          source.dietaryRestrictions.isNotEmpty ? source.dietaryRestrictions : null,
      healthConditions:
          source.healthConditions.isNotEmpty ? source.healthConditions : null,
      sensoryDisabilities:
          source.sensoryDisabilities.isNotEmpty ? source.sensoryDisabilities : null,
      emergencyContactName: ecName,
      emergencyContactPhone: ecPhone,
      emergencyContactRelationship: ecRelation,
      acceptedDataProcessing: source.acceptedDataProcessing,
      acceptedMediaUsage: _parseBool(source.acceptedMediaUsage),
      acceptedRiskRelease: _parseBool(source.acceptedRiskRelease),
      isCompleted: source.isCompleted,
    );
  }

  /// Parse 'true'/'false' String → bool? 
  static bool? _parseBool(String value) {
    if (value == 'true') return true;
    if (value == 'false') return false;
    return null;
  }

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
