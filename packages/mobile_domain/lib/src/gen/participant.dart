// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantResponseSchema`.

class Participant {

  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String reservationId;
  final String firstName;
  final String lastName;
  final DateTime birthDate;  // date-only (no time)
  final String documentType;
  final String documentNumber;
  final String phone;
  final String country;
  final String? countryCode;
  final String? countryName;
  final String city;
  final String heightCm;
  final String weightKg;
  final String? experienceLevel;
  final String dietaryRestrictions;
  final String bloodType;
  final String epsOrTravelInsurance;
  final String healthConditions;
  final String sensoryDisabilities;
  final String? emergencyContact;
  final bool acceptedDataProcessing;
  final String acceptedMediaUsage;
  final String acceptedRiskRelease;
  final String riskReleaseTextVersion;
  final bool isCompleted;

  const Participant(
    {
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.reservationId,
    required this.firstName,
    required this.lastName,
    required this.birthDate,
    required this.documentType,
    required this.documentNumber,
    required this.phone,
    required this.country,
    this.countryCode,
    this.countryName,
    required this.city,
    required this.heightCm,
    required this.weightKg,
    this.experienceLevel,
    required this.dietaryRestrictions,
    required this.bloodType,
    required this.epsOrTravelInsurance,
    required this.healthConditions,
    required this.sensoryDisabilities,
    this.emergencyContact,
    required this.acceptedDataProcessing,
    required this.acceptedMediaUsage,
    required this.acceptedRiskRelease,
    required this.riskReleaseTextVersion,
    required this.isCompleted,
    }
  );

  factory Participant.fromJson(Map<String, dynamic> json) {
    return Participant(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      reservationId: json['reservation_id'] as String,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      birthDate: DateTime.parse(json['birth_date'] as String),
      documentType: json['document_type'] as String,
      documentNumber: json['document_number'] as String,
      phone: json['phone'] as String,
      country: json['country'] as String,
      countryCode: json['country_code'] as String?,
      countryName: json['country_name'] as String?,
      city: json['city'] as String,
      heightCm: json['height_cm'] as String,
      weightKg: json['weight_kg'] as String,
      experienceLevel: json['experience_level'] as String?,
      dietaryRestrictions: json['dietary_restrictions'] as String,
      bloodType: json['blood_type'] as String,
      epsOrTravelInsurance: json['eps_or_travel_insurance'] as String,
      healthConditions: json['health_conditions'] as String,
      sensoryDisabilities: json['sensory_disabilities'] as String,
      emergencyContact: json['emergency_contact'] as String?,
      acceptedDataProcessing: json['accepted_data_processing'] as bool,
      acceptedMediaUsage: json['accepted_media_usage'] as String,
      acceptedRiskRelease: json['accepted_risk_release'] as String,
      riskReleaseTextVersion: json['risk_release_text_version'] as String,
      isCompleted: json['is_completed'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'reservation_id': reservationId,
    'first_name': firstName,
    'last_name': lastName,
    'birth_date': birthDate.toIso8601String(),
    'document_type': documentType,
    'document_number': documentNumber,
    'phone': phone,
    'country': country,
    'country_code': countryCode,
    'country_name': countryName,
    'city': city,
    'height_cm': heightCm,
    'weight_kg': weightKg,
    'experience_level': experienceLevel,
    'dietary_restrictions': dietaryRestrictions,
    'blood_type': bloodType,
    'eps_or_travel_insurance': epsOrTravelInsurance,
    'health_conditions': healthConditions,
    'sensory_disabilities': sensoryDisabilities,
    'emergency_contact': emergencyContact,
    'accepted_data_processing': acceptedDataProcessing,
    'accepted_media_usage': acceptedMediaUsage,
    'accepted_risk_release': acceptedRiskRelease,
    'risk_release_text_version': riskReleaseTextVersion,
    'is_completed': isCompleted,
  };

}
