// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineCreateSchema`.

import 'equine_location_status.dart';
import 'equine_operational_status.dart';
import 'equine_sex.dart';
import 'equine_species.dart';

class EquineCreate {
  final String name;
  final String? inventoryNumber;
  final EquineSpecies? species;
  final EquineLocationStatus? locationStatus;
  final String? locationNotes;
  final String? breed;
  final EquineSex? sex;
  final String? coatColor;
  final String? gait;
  final String? approximateBirthDate;
  final String? approximateAgeYears;
  final bool? birthDateIsApproximate;
  final String? birthDateRaw;
  final String? birthPlace;
  final String? registryNumber;
  final String? microchip;
  final String? sireName;
  final String? damName;
  final String? weightKg;
  final String? heightM;
  final String? lastWeightAt;
  final String? lastHeightAt;
  final bool? isActive;
  final bool? isAvailable;
  final EquineOperationalStatus? operationalStatus;
  final String? availabilityNotes;
  final String? availabilityReasons;
  final String? restUntil;
  final String? maxRiderWeightKg;
  final String? experienceFit;
  final String? imageBase64;
  final String? lastServiceAt;
  final int? workloadLast7Days;
  final String? sourceFile;
  final String? sourceSheet;
  final String? sourceRowNumber;
  final String? sourceUpdatedAtLabel;

  const EquineCreate({
    required this.name,
    this.inventoryNumber,
    this.species,
    this.locationStatus,
    this.locationNotes,
    this.breed,
    this.sex,
    this.coatColor,
    this.gait,
    this.approximateBirthDate,
    this.approximateAgeYears,
    this.birthDateIsApproximate,
    this.birthDateRaw,
    this.birthPlace,
    this.registryNumber,
    this.microchip,
    this.sireName,
    this.damName,
    this.weightKg,
    this.heightM,
    this.lastWeightAt,
    this.lastHeightAt,
    this.isActive,
    this.isAvailable,
    this.operationalStatus,
    this.availabilityNotes,
    this.availabilityReasons,
    this.restUntil,
    this.maxRiderWeightKg,
    this.experienceFit,
    this.imageBase64,
    this.lastServiceAt,
    this.workloadLast7Days,
    this.sourceFile,
    this.sourceSheet,
    this.sourceRowNumber,
    this.sourceUpdatedAtLabel,
  });

  factory EquineCreate.fromJson(Map<String, dynamic> json) {
    return EquineCreate(
      name: json['name'] as String,
      inventoryNumber: json['inventory_number'] as String?,
      species: json['species'] != null
          ? (json['species'] as String).toEquineSpecies()
          : null,
      locationStatus: json['location_status'] != null
          ? (json['location_status'] as String).toEquineLocationStatus()
          : null,
      locationNotes: json['location_notes'] as String?,
      breed: json['breed'] as String?,
      sex: json['sex'] != null ? (json['sex'] as String).toEquineSex() : null,
      coatColor: json['coat_color'] as String?,
      gait: json['gait'] as String?,
      approximateBirthDate: json['approximate_birth_date'] as String?,
      approximateAgeYears: json['approximate_age_years'] as String?,
      birthDateIsApproximate: json['birth_date_is_approximate'] as bool?,
      birthDateRaw: json['birth_date_raw'] as String?,
      birthPlace: json['birth_place'] as String?,
      registryNumber: json['registry_number'] as String?,
      microchip: json['microchip'] as String?,
      sireName: json['sire_name'] as String?,
      damName: json['dam_name'] as String?,
      weightKg: json['weight_kg'] as String?,
      heightM: json['height_m'] as String?,
      lastWeightAt: json['last_weight_at'] as String?,
      lastHeightAt: json['last_height_at'] as String?,
      isActive: json['is_active'] as bool?,
      isAvailable: json['is_available'] as bool?,
      operationalStatus: json['operational_status'] != null
          ? (json['operational_status'] as String).toEquineOperationalStatus()
          : null,
      availabilityNotes: json['availability_notes'] as String?,
      availabilityReasons: json['availability_reasons'] as String?,
      restUntil: json['rest_until'] as String?,
      maxRiderWeightKg: json['max_rider_weight_kg'] as String?,
      experienceFit: json['experience_fit'] as String?,
      imageBase64: json['image_base64'] as String?,
      lastServiceAt: json['last_service_at'] as String?,
      workloadLast7Days: json['workload_last_7_days'] as int?,
      sourceFile: json['source_file'] as String?,
      sourceSheet: json['source_sheet'] as String?,
      sourceRowNumber: json['source_row_number'] as String?,
      sourceUpdatedAtLabel: json['source_updated_at_label'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'inventory_number': inventoryNumber,
    'species': species?.toJson(),
    'location_status': locationStatus?.toJson(),
    'location_notes': locationNotes,
    'breed': breed,
    'sex': sex?.toJson(),
    'coat_color': coatColor,
    'gait': gait,
    'approximate_birth_date': approximateBirthDate,
    'approximate_age_years': approximateAgeYears,
    'birth_date_is_approximate': birthDateIsApproximate,
    'birth_date_raw': birthDateRaw,
    'birth_place': birthPlace,
    'registry_number': registryNumber,
    'microchip': microchip,
    'sire_name': sireName,
    'dam_name': damName,
    'weight_kg': weightKg,
    'height_m': heightM,
    'last_weight_at': lastWeightAt,
    'last_height_at': lastHeightAt,
    'is_active': isActive,
    'is_available': isAvailable,
    'operational_status': operationalStatus?.toJson(),
    'availability_notes': availabilityNotes,
    'availability_reasons': availabilityReasons,
    'rest_until': restUntil,
    'max_rider_weight_kg': maxRiderWeightKg,
    'experience_fit': experienceFit,
    'image_base64': imageBase64,
    'last_service_at': lastServiceAt,
    'workload_last_7_days': workloadLast7Days,
    'source_file': sourceFile,
    'source_sheet': sourceSheet,
    'source_row_number': sourceRowNumber,
    'source_updated_at_label': sourceUpdatedAtLabel,
  };
}
