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
      inventoryNumber: _parseInt(json['inventory_number']),
      species: json['species'] as String? ?? 'mule',
      locationStatus: json['location_status'] as String? ?? 'la_juana',
      locationNotes: json['location_notes'] as String?,
      breed: json['breed'] as String?,
      sex: json['sex'] as String? ?? 'unknown',
      coatColor: json['coat_color'] as String?,
      gait: json['gait'] as String?,
      approximateBirthDate: json['approximate_birth_date'] as String?,
      approximateAgeYears: _parseInt(json['approximate_age_years']),
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
      workloadLast7Days: _parseInt(json['workload_last_7_days']) ?? 0,
      imageBase64: json['image_base64'] as String?,
      sourceFile: json['source_file'] as String?,
      sourceSheet: json['source_sheet'] as String?,
      sourceRowNumber: _parseInt(json['source_row_number']),
      sourceUpdatedAtLabel: json['source_updated_at_label'] as String?,
      version: _parseInt(json['version']) ?? 1,
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

  /// Safe [int] parser that handles [String] values from Pydantic v2.
  static int? _parseInt(Object? value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is String) {
      final trimmed = value.trim();
      if (trimmed.isEmpty) return null;
      return int.tryParse(trimmed);
    }
    return null;
  }

  /// Serializa de vuelta al formato JSON snake_case que espera gen.Equine.fromJson.
  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt ?? '',
    'updated_at': updatedAt ?? '',
    'deleted_at': deletedAt,
    'id': id,
    'name': name,
    'inventory_number': inventoryNumber?.toString() ?? '',
    'species': species,
    'location_status': locationStatus,
    'location_notes': locationNotes ?? '',
    'breed': breed ?? '',
    'sex': sex,
    'coat_color': coatColor ?? '',
    'gait': gait ?? '',
    'approximate_birth_date': approximateBirthDate ?? '',
    'approximate_age_years': approximateAgeYears?.toString() ?? '',
    'birth_date_is_approximate': birthDateIsApproximate,
    'birth_date_raw': birthDateRaw ?? '',
    'birth_place': birthPlace ?? '',
    'registry_number': registryNumber ?? '',
    'microchip': microchip ?? '',
    'sire_name': sireName ?? '',
    'dam_name': damName ?? '',
    'weight_kg': weightKg?.toString() ?? '',
    'height_m': heightM?.toString() ?? '',
    'last_weight_at': lastWeightAt ?? '',
    'last_height_at': lastHeightAt ?? '',
    'is_active': isActive,
    'is_available': isAvailable,
    'operational_status': operationalStatus,
    'availability_notes': availabilityNotes ?? '',
    'availability_reasons': availabilityReasons ?? '',
    'rest_until': restUntil ?? '',
    'max_rider_weight_kg': maxRiderWeightKg?.toString() ?? '',
    'experience_fit': experienceFit ?? '',
    'last_service_at': lastServiceAt,
    'workload_last_7_days': workloadLast7Days,
    'image_base64': imageBase64,
    'source_file': sourceFile ?? '',
    'source_sheet': sourceSheet ?? '',
    'source_row_number': sourceRowNumber?.toString() ?? '',
    'source_updated_at_label': sourceUpdatedAtLabel ?? '',
  };
}

/// DTO para una entrada del timeline del equino desde la API.
class EquineTimelineEntryDto {
  EquineTimelineEntryDto({
    required this.id,
    required this.source,
    required this.eventType,
    required this.happenedAt,
    required this.title,
    this.reservationId,
    this.notes,
    this.severity,
    this.affectsAvailability = false,
  });

  final String id;
  final String source;
  final String eventType;
  final String happenedAt;
  final String title;
  final String? reservationId;
  final String? notes;
  final String? severity;
  final bool affectsAvailability;

  factory EquineTimelineEntryDto.fromJson(Map<String, dynamic> json) {
    return EquineTimelineEntryDto(
      id: json['id'] as String? ?? '',
      source: json['source'] as String? ?? 'service_log',
      eventType: json['event_type'] as String? ?? '',
      happenedAt: json['happened_at'] as String? ?? '',
      title: json['title'] as String? ?? '',
      reservationId: json['reservation_id'] as String?,
      notes: json['notes'] as String?,
      severity: json['severity'] as String?,
      affectsAvailability: json['affects_availability'] as bool? ?? false,
    );
  }
}

/// DTO de respuesta al crear/consultar un evento de equino.
class EquineEventDto {
  EquineEventDto({
    required this.id,
    required this.equineId,
    required this.eventType,
    required this.happenedAt,
    required this.title,
    this.description,
    this.severity,
    this.measuredWeightKg,
    this.nextDueAt,
    this.performedBy,
    this.affectsAvailability = false,
    this.resultingOperationalStatus,
    this.restUntil,
  });

  final String id;
  final String equineId;
  final String eventType;
  final String happenedAt;
  final String title;
  final String? description;
  final String? severity;
  final double? measuredWeightKg;
  final String? nextDueAt;
  final String? performedBy;
  final bool affectsAvailability;
  final String? resultingOperationalStatus;
  final String? restUntil;

  factory EquineEventDto.fromJson(Map<String, dynamic> json) {
    return EquineEventDto(
      id: json['id'] as String? ?? '',
      equineId: json['equine_id'] as String? ?? '',
      eventType: json['event_type'] as String? ?? '',
      happenedAt: json['happened_at'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String?,
      severity: json['severity'] as String?,
      measuredWeightKg: EquineDto._parseDecimal(json['measured_weight_kg']),
      nextDueAt: json['next_due_at'] as String?,
      performedBy: json['performed_by'] as String?,
      affectsAvailability: json['affects_availability'] as bool? ?? false,
      resultingOperationalStatus:
          json['resulting_operational_status'] as String?,
      restUntil: json['rest_until'] as String?,
    );
  }
}
