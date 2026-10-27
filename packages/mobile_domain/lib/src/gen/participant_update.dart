// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantUpdateSchema`.

class ParticipantUpdate {
  final String? firstName;
  final String? lastName;
  final String? email;
  final String? birthDate;
  final String? phone;
  final String? country;
  final String? city;
  final String? heightCm;
  final String? weightKg;
  final String? dietaryRestrictions;
  final String? bloodType;
  final String? epsOrTravelInsurance;
  final String? healthConditions;
  final String? sensoryDisabilities;
  final String? emergencyContact;
  final String? acceptedDataProcessing;
  final String? acceptedMediaUsage;
  final String? acceptedRiskRelease;
  final String? riskReleaseTextVersion;

  const ParticipantUpdate({
    this.firstName,
    this.lastName,
    this.email,
    this.birthDate,
    this.phone,
    this.country,
    this.city,
    this.heightCm,
    this.weightKg,
    this.dietaryRestrictions,
    this.bloodType,
    this.epsOrTravelInsurance,
    this.healthConditions,
    this.sensoryDisabilities,
    this.emergencyContact,
    this.acceptedDataProcessing,
    this.acceptedMediaUsage,
    this.acceptedRiskRelease,
    this.riskReleaseTextVersion,
  });

  factory ParticipantUpdate.fromJson(Map<String, dynamic> json) {
    return ParticipantUpdate(
      firstName: json['first_name'] as String?,
      lastName: json['last_name'] as String?,
      email: json['email'] as String?,
      birthDate: json['birth_date'] as String?,
      phone: json['phone'] as String?,
      country: json['country'] as String?,
      city: json['city'] as String?,
      heightCm: json['height_cm'] as String?,
      weightKg: json['weight_kg'] as String?,
      dietaryRestrictions: json['dietary_restrictions'] as String?,
      bloodType: json['blood_type'] as String?,
      epsOrTravelInsurance: json['eps_or_travel_insurance'] as String?,
      healthConditions: json['health_conditions'] as String?,
      sensoryDisabilities: json['sensory_disabilities'] as String?,
      emergencyContact: json['emergency_contact'] as String?,
      acceptedDataProcessing: json['accepted_data_processing'] as String?,
      acceptedMediaUsage: json['accepted_media_usage'] as String?,
      acceptedRiskRelease: json['accepted_risk_release'] as String?,
      riskReleaseTextVersion: json['risk_release_text_version'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'first_name': firstName,
    'last_name': lastName,
    'email': email,
    'birth_date': birthDate,
    'phone': phone,
    'country': country,
    'city': city,
    'height_cm': heightCm,
    'weight_kg': weightKg,
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
  };
}
