/// DTO completo para un equino desde la API.
class EquineDto {
  EquineDto({
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
    this.birthDateIsApproximate = true,
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
    this.isActive = true,
    this.isAvailable = true,
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
    this.createdAt,
    this.updatedAt,
    this.deletedAt,
    this.imageBase64,
  });

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
  final bool birthDateIsApproximate;
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
  final bool isActive;
  final bool isAvailable;
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
  final String? createdAt;
  final String? updatedAt;
  final String? deletedAt;
  final String? imageBase64;

  factory EquineDto.fromJson(Map<String, dynamic> json) {
    return EquineDto(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      inventoryNumber: json['inventory_number'] as int?,
      species: json['species'] as String? ?? 'mule',
      locationStatus: json['location_status'] as String? ?? 'la_juana',
      locationNotes: json['location_notes'] as String?,
      breed: json['breed'] as String?,
      sex: json['sex'] as String? ?? 'unknown',
      coatColor: json['coat_color'] as String?,
      gait: json['gait'] as String?,
      approximateBirthDate: json['approximate_birth_date'] as String?,
      approximateAgeYears: json['approximate_age_years'] as int?,
      birthDateIsApproximate:
          json['birth_date_is_approximate'] as bool? ?? true,
      birthDateRaw: json['birth_date_raw'] as String?,
      birthPlace: json['birth_place'] as String?,
      registryNumber: json['registry_number'] as String?,
      microchip: json['microchip'] as String?,
      sireName: json['sire_name'] as String?,
      damName: json['dam_name'] as String?,
      weightKg: _parseDecimal(json['weight_kg']),
      heightM: _parseDecimal(json['height_m']),
      lastWeightAt: json['last_weight_at'] as String?,
      lastHeightAt: json['last_height_at'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      isAvailable: json['is_available'] as bool? ?? true,
      operationalStatus:
          json['operational_status'] as String? ?? 'available',
      availabilityNotes: json['availability_notes'] as String?,
      availabilityReasons: json['availability_reasons'] as String?,
      restUntil: json['rest_until'] as String?,
      maxRiderWeightKg: _parseDecimal(json['max_rider_weight_kg']),
      experienceFit: json['experience_fit'] as String?,
      lastServiceAt: json['last_service_at'] as String?,
      workloadLast7Days: json['workload_last_7_days'] as int? ?? 0,
      imageBase64: json['image_base64'] as String?,
      sourceFile: json['source_file'] as String?,
      sourceSheet: json['source_sheet'] as String?,
      sourceRowNumber: json['source_row_number'] as int?,
      sourceUpdatedAtLabel: json['source_updated_at_label'] as String?,
      version: json['version'] as int? ?? 1,
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
      deletedAt: json['deleted_at'] as String?,
    );
  }

  /// Pydantic v2 serializa Decimal como String. Parseamos ambos casos.
  static double? _parseDecimal(Object? value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    if (value is String) {
      final trimmed = value.trim();
      if (trimmed.isEmpty) return null;
      return double.tryParse(trimmed);
    }
    return null;
  }
}
