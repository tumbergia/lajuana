import '../../presentation/models/equine_view_models.dart';

/// Registro SQLite plano para el caché local de equinos.
class EquineLocalRecord {
  EquineLocalRecord({
    required this.id,
    required this.name,
    this.inventoryNumber,
    this.species = 'mule',
    this.locationStatus = 'la_juana',
    this.locationNotes,
    this.breed,
    this.sex = 'unknown',
    this.coatColor,
    this.gait,
    this.approximateBirthDate,
    this.approximateAgeYears,
    this.birthDateIsApproximate = 1,
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
    this.isActive = 1,
    this.isAvailable = 1,
    this.operationalStatus = 'available',
    this.availabilityNotes,
    this.availabilityReasons,
    this.restUntil,
    this.maxRiderWeightKg,
    this.experienceFit,
    this.lastServiceAt,
    this.workloadLast7Days = 0,
    this.sourceFile,
    this.sourceSheet,
    this.sourceRowNumber,
    this.sourceUpdatedAtLabel,
    this.version = 1,
    this.updatedAt,
  });

  // ... (all fields as before)
  final String id;
  final String name;
  final int? inventoryNumber;
  final String species;
  final String locationStatus;
  final String? locationNotes;
  final String? breed;
  final String sex;
  final String? coatColor;
  final String? gait;
  final String? approximateBirthDate;
  final int? approximateAgeYears;
  final int birthDateIsApproximate;
  final String? birthDateRaw;
  final String? birthPlace;
  final String? registryNumber;
  final String? microchip;
  final String? sireName;
  final String? damName;
  final double? weightKg;
  final double? heightM;
  final String? lastWeightAt;
  final String? lastHeightAt;
  final int isActive;
  final int isAvailable;
  final String operationalStatus;
  final String? availabilityNotes;
  final String? availabilityReasons;
  final String? restUntil;
  final double? maxRiderWeightKg;
  final String? experienceFit;
  final String? lastServiceAt;
  final int workloadLast7Days;
  final String? sourceFile;
  final String? sourceSheet;
  final int? sourceRowNumber;
  final String? sourceUpdatedAtLabel;
  final int version;
  final String? updatedAt;

  factory EquineLocalRecord.fromMap(Map<String, Object?> map) {
    return EquineLocalRecord(
      id: map['id'] as String? ?? '',
      name: map['name'] as String? ?? '',
      inventoryNumber: map['inventory_number'] as int?,
      species: map['species'] as String? ?? 'mule',
      locationStatus: map['location_status'] as String? ?? 'la_juana',
      locationNotes: map['location_notes'] as String?,
      breed: map['breed'] as String?,
      sex: map['sex'] as String? ?? 'unknown',
      coatColor: map['coat_color'] as String?,
      gait: map['gait'] as String?,
      approximateBirthDate: map['approximate_birth_date'] as String?,
      approximateAgeYears: map['approximate_age_years'] as int?,
      birthDateIsApproximate: (map['birth_date_is_approximate'] as int? ?? 1),
      birthDateRaw: map['birth_date_raw'] as String?,
      birthPlace: map['birth_place'] as String?,
      registryNumber: map['registry_number'] as String?,
      microchip: map['microchip'] as String?,
      sireName: map['sire_name'] as String?,
      damName: map['dam_name'] as String?,
      weightKg: (map['weight_kg'] as num?)?.toDouble(),
      heightM: (map['height_m'] as num?)?.toDouble(),
      lastWeightAt: map['last_weight_at'] as String?,
      lastHeightAt: map['last_height_at'] as String?,
      isActive: (map['is_active'] as int? ?? 1),
      isAvailable: (map['is_available'] as int? ?? 1),
      operationalStatus: map['operational_status'] as String? ?? 'available',
      availabilityNotes: map['availability_notes'] as String?,
      availabilityReasons: map['availability_reasons'] as String?,
      restUntil: map['rest_until'] as String?,
      maxRiderWeightKg: (map['max_rider_weight_kg'] as num?)?.toDouble(),
      experienceFit: map['experience_fit'] as String?,
      lastServiceAt: map['last_service_at'] as String?,
      workloadLast7Days: map['workload_last_7_days'] as int? ?? 0,
      sourceFile: map['source_file'] as String?,
      sourceSheet: map['source_sheet'] as String?,
      sourceRowNumber: map['source_row_number'] as int?,
      sourceUpdatedAtLabel: map['source_updated_at_label'] as String?,
      version: map['version'] as int? ?? 1,
      updatedAt: map['updated_at'] as String?,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'name': name,
      'inventory_number': inventoryNumber,
      'species': species,
      'location_status': locationStatus,
      'location_notes': locationNotes,
      'breed': breed,
      'sex': sex,
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
      'operational_status': operationalStatus,
      'availability_notes': availabilityNotes,
      'availability_reasons': availabilityReasons,
      'rest_until': restUntil,
      'max_rider_weight_kg': maxRiderWeightKg,
      'experience_fit': experienceFit,
      'last_service_at': lastServiceAt,
      'workload_last_7_days': workloadLast7Days,
      'source_file': sourceFile,
      'source_sheet': sourceSheet,
      'source_row_number': sourceRowNumber,
      'source_updated_at_label': sourceUpdatedAtLabel,
      'version': version,
      'updated_at': updatedAt,
    };
  }

  static EquineLocalRecord fromDetail(EquineDetailRecord detail) {
    return EquineLocalRecord(
      id: detail.id,
      name: detail.name,
      inventoryNumber: detail.inventoryNumber,
      species: detail.species,
      locationStatus: detail.locationStatus,
      locationNotes: detail.locationNotes,
      breed: detail.breed,
      sex: detail.sex,
      coatColor: detail.coatColor,
      gait: detail.gait,
      approximateBirthDate: detail.approximateBirthDate,
      approximateAgeYears: detail.approximateAgeYears,
      birthDateIsApproximate: detail.birthDateIsApproximate ? 1 : 0,
      birthDateRaw: detail.birthDateRaw,
      birthPlace: detail.birthPlace,
      registryNumber: detail.registryNumber,
      microchip: detail.microchip,
      sireName: detail.sireName,
      damName: detail.damName,
      weightKg: detail.weightKg,
      heightM: detail.heightM,
      lastWeightAt: detail.lastWeightAt,
      lastHeightAt: detail.lastHeightAt,
      isActive: detail.isActive ? 1 : 0,
      isAvailable: detail.isAvailable ? 1 : 0,
      operationalStatus: detail.operationalStatus.name,
      availabilityNotes: detail.availabilityNotes,
      availabilityReasons: detail.availabilityReasons,
      restUntil: detail.restUntil?.toIso8601String(),
      maxRiderWeightKg: detail.maxRiderWeightKg,
      experienceFit: detail.experienceFit?.name,
      lastServiceAt: detail.lastServiceAt?.toIso8601String(),
      workloadLast7Days: detail.workloadLast7Days,
      version: 1,
      updatedAt: detail.updatedAt?.toIso8601String(),
    );
  }
}
