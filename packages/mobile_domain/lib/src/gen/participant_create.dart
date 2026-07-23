// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantCreateSchema`.

import 'emergency_contact.dart';
import 'experience_level.dart';

class ParticipantCreate {
  final String firstName;
  final String lastName;
  final String? email;
  final DateTime birthDate; // date-only (no time)
  final String documentType;
  final String documentNumber;
  final String phone;
  final String country;
  final String city;
  final String heightCm;
  final String weightKg;
  final ExperienceLevel experienceLevel;
  final String? dietaryRestrictions;
  final String? bloodType;
  final String? epsOrTravelInsurance;
  final String? healthConditions;
  final String? sensoryDisabilities;
  final EmergencyContact emergencyContact;
  final bool acceptedDataProcessing;
  final String? acceptedMediaUsage;
  final String? acceptedRiskRelease;
  final String? riskReleaseTextVersion;

  const ParticipantCreate({
    required this.firstName,
    required this.lastName,
    this.email,
    required this.birthDate,
    required this.documentType,
    required this.documentNumber,
    required this.phone,
    required this.country,
    required this.city,
    required this.heightCm,
    required this.weightKg,
    required this.experienceLevel,
    this.dietaryRestrictions,
    this.bloodType,
    this.epsOrTravelInsurance,
    this.healthConditions,
    this.sensoryDisabilities,
    required this.emergencyContact,
    required this.acceptedDataProcessing,
    this.acceptedMediaUsage,
    this.acceptedRiskRelease,
    this.riskReleaseTextVersion,
  });

  factory ParticipantCreate.fromJson(Map<String, dynamic> json) {
    return ParticipantCreate(
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      email: json['email'] as String?,
      birthDate: DateTime.parse(json['birth_date'] as String),
      documentType: json['document_type'] as String,
      documentNumber: json['document_number'] as String,
      phone: json['phone'] as String,
      country: json['country'] as String,
      city: json['city'] as String,
      heightCm: json['height_cm'] as String,
      weightKg: json['weight_kg'] as String,
      experienceLevel: (json['experience_level'] as String).toExperienceLevel(),
      dietaryRestrictions: json['dietary_restrictions'] as String?,
      bloodType: json['blood_type'] as String?,
      epsOrTravelInsurance: json['eps_or_travel_insurance'] as String?,
      healthConditions: json['health_conditions'] as String?,
      sensoryDisabilities: json['sensory_disabilities'] as String?,
      emergencyContact: EmergencyContact.fromJson(
        json['emergency_contact'] as Map<String, dynamic>,
      ),
      acceptedDataProcessing: json['accepted_data_processing'] as bool,
      acceptedMediaUsage: json['accepted_media_usage'] as String?,
      acceptedRiskRelease: json['accepted_risk_release'] as String?,
      riskReleaseTextVersion: json['risk_release_text_version'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'first_name': firstName,
    'last_name': lastName,
    'email': email,
    'birth_date': birthDate.toIso8601String(),
    'document_type': documentType,
    'document_number': documentNumber,
    'phone': phone,
    'country': country,
    'city': city,
    'height_cm': heightCm,
    'weight_kg': weightKg,
    'experience_level': experienceLevel.toJson(),
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
