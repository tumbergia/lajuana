// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ParticipantPublicCreateSchema`.

import 'experience_level.dart';

class ParticipantPublicCreate {

  final String firstName;
  final String lastName;
  final String? email;
  final DateTime birthDate;  // date-only (no time)
  final String documentType;
  final String documentNumber;
  final String phone;
  final String country;
  final String city;
  final String heightCm;
  final String weightKg;
  final ExperienceLevel experienceLevel;
  final String? bloodType;
  final String? eps;
  final String? travelInsurance;
  final String? medicalConditions;
  final String? functionalConditions;
  final String? dietaryRestrictions;
  final String? diet;
  final String emergencyContactName;
  final String emergencyContactPhone;
  final String? emergencyContactRelationship;
  final String? emergencyContactCountry;
  final bool acceptedDataProcessing;
  final String? acceptedMediaUsage;
  final bool acceptedRiskRelease;
  final String? riskReleaseTextVersion;

  const ParticipantPublicCreate(
    {
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
    this.bloodType,
    this.eps,
    this.travelInsurance,
    this.medicalConditions,
    this.functionalConditions,
    this.dietaryRestrictions,
    this.diet,
    required this.emergencyContactName,
    required this.emergencyContactPhone,
    this.emergencyContactRelationship,
    this.emergencyContactCountry,
    required this.acceptedDataProcessing,
    this.acceptedMediaUsage,
    required this.acceptedRiskRelease,
    this.riskReleaseTextVersion,
    }
  );

  factory ParticipantPublicCreate.fromJson(Map<String, dynamic> json) {
    return ParticipantPublicCreate(
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
      bloodType: json['blood_type'] as String?,
      eps: json['eps'] as String?,
      travelInsurance: json['travel_insurance'] as String?,
      medicalConditions: json['medical_conditions'] as String?,
      functionalConditions: json['functional_conditions'] as String?,
      dietaryRestrictions: json['dietary_restrictions'] as String?,
      diet: json['diet'] as String?,
      emergencyContactName: json['emergency_contact_name'] as String,
      emergencyContactPhone: json['emergency_contact_phone'] as String,
      emergencyContactRelationship: json['emergency_contact_relationship'] as String?,
      emergencyContactCountry: json['emergency_contact_country'] as String?,
      acceptedDataProcessing: json['accepted_data_processing'] as bool,
      acceptedMediaUsage: json['accepted_media_usage'] as String?,
      acceptedRiskRelease: json['accepted_risk_release'] as bool,
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
    'blood_type': bloodType,
    'eps': eps,
    'travel_insurance': travelInsurance,
    'medical_conditions': medicalConditions,
    'functional_conditions': functionalConditions,
    'dietary_restrictions': dietaryRestrictions,
    'diet': diet,
    'emergency_contact_name': emergencyContactName,
    'emergency_contact_phone': emergencyContactPhone,
    'emergency_contact_relationship': emergencyContactRelationship,
    'emergency_contact_country': emergencyContactCountry,
    'accepted_data_processing': acceptedDataProcessing,
    'accepted_media_usage': acceptedMediaUsage,
    'accepted_risk_release': acceptedRiskRelease,
    'risk_release_text_version': riskReleaseTextVersion,
  };

}
