// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EquineListItemSchema`.

import 'equine_location_status.dart';
import 'equine_operational_status.dart';
import 'equine_sex.dart';
import 'equine_species.dart';

class EquineListItem {

  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String name;
  final String inventoryNumber;
  final EquineSpecies species;
  final EquineLocationStatus? locationStatus;
  final String? locationNotes;
  final String breed;
  final EquineSex sex;
  final String coatColor;
  final String gait;
  final String weightKg;
  final String heightM;
  final bool isActive;
  final bool isAvailable;
  final EquineOperationalStatus operationalStatus;
  final String? approximateAgeYears;
  final String maxRiderWeightKg;
  final String experienceFit;
  final String? imageBase64;
  final String? lastServiceAt;
  final int workloadLast7Days;
  final String? restUntil;
  final String? availabilityReasons;
  final String? blockReason;

  const EquineListItem(
    {
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.name,
    required this.inventoryNumber,
    required this.species,
    this.locationStatus,
    this.locationNotes,
    required this.breed,
    required this.sex,
    required this.coatColor,
    required this.gait,
    required this.weightKg,
    required this.heightM,
    required this.isActive,
    required this.isAvailable,
    required this.operationalStatus,
    this.approximateAgeYears,
    required this.maxRiderWeightKg,
    required this.experienceFit,
    this.imageBase64,
    this.lastServiceAt,
    required this.workloadLast7Days,
    this.restUntil,
    this.availabilityReasons,
    this.blockReason,
    }
  );

  factory EquineListItem.fromJson(Map<String, dynamic> json) {
    return EquineListItem(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      name: json['name'] as String,
      inventoryNumber: json['inventory_number'] as String,
      species: (json['species'] as String).toEquineSpecies(),
      locationStatus: json['location_status'] != null ? (json['location_status'] as String).toEquineLocationStatus() : null,
      locationNotes: json['location_notes'] as String?,
      breed: json['breed'] as String,
      sex: (json['sex'] as String).toEquineSex(),
      coatColor: json['coat_color'] as String,
      gait: json['gait'] as String,
      weightKg: json['weight_kg'] as String,
      heightM: json['height_m'] as String,
      isActive: json['is_active'] as bool,
      isAvailable: json['is_available'] as bool,
      operationalStatus: (json['operational_status'] as String).toEquineOperationalStatus(),
      approximateAgeYears: json['approximate_age_years'] as String?,
      maxRiderWeightKg: json['max_rider_weight_kg'] as String,
      experienceFit: json['experience_fit'] as String,
      imageBase64: json['image_base64'] as String?,
      lastServiceAt: json['last_service_at'] as String?,
      workloadLast7Days: json['workload_last_7_days'] as int,
      restUntil: json['rest_until'] as String?,
      availabilityReasons: json['availability_reasons'] as String?,
      blockReason: json['block_reason'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'name': name,
    'inventory_number': inventoryNumber,
    'species': species.toJson(),
    'location_status': locationStatus?.toJson(),
    'location_notes': locationNotes,
    'breed': breed,
    'sex': sex.toJson(),
    'coat_color': coatColor,
    'gait': gait,
    'weight_kg': weightKg,
    'height_m': heightM,
    'is_active': isActive,
    'is_available': isAvailable,
    'operational_status': operationalStatus.toJson(),
    'approximate_age_years': approximateAgeYears,
    'max_rider_weight_kg': maxRiderWeightKg,
    'experience_fit': experienceFit,
    'image_base64': imageBase64,
    'last_service_at': lastServiceAt,
    'workload_last_7_days': workloadLast7Days,
    'rest_until': restUntil,
    'availability_reasons': availabilityReasons,
    'block_reason': blockReason,
  };

}
