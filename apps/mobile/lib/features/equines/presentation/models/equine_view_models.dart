import '../../domain/models/equine_experience_fit.dart';
import '../../domain/models/equine_operational_status.dart';
import '../../../../app/widgets/app_badge.dart';

/// ViewModel ligero para el listado de equinos.
class EquineRecord {
  EquineRecord({
    required this.id,
    required this.name,
    this.inventoryNumber,
    this.species = 'mule',
    this.breed,
    this.sex = 'unknown',
    required this.statusLabel,
    required this.statusTone,
    required this.summary,
    this.subtitle,
    this.isAvailable = true,
    this.weightKg,
    this.imageBase64,
  });

  final String id;
  final String name;
  final int? inventoryNumber;
  final String species;
  final String? breed;
  final String sex;
  final String statusLabel;
  final AppBadgeTone statusTone;
  final String summary;
  final String? subtitle;
  final bool isAvailable;
  final double? weightKg;
  final String? imageBase64;
}

/// ViewModel completo para el detalle de equino.
class EquineDetailRecord {
  EquineDetailRecord({
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
    required this.operationalStatus,
    required this.statusLabel,
    required this.statusTone,
    this.availabilityNotes,
    this.availabilityReasons,
    this.restUntil,
    this.maxRiderWeightKg,
    this.experienceFit,
    this.lastServiceAt,
    this.workloadLast7Days = 0,
    this.updatedAt,
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
  final EquineOperationalStatus operationalStatus;
  final String statusLabel;
  final AppBadgeTone statusTone;
  final String? availabilityNotes;
  final String? availabilityReasons;
  final DateTime? restUntil;
  final double? maxRiderWeightKg;
  final EquineExperienceFit? experienceFit;
  final DateTime? lastServiceAt;
  final int workloadLast7Days;
  final DateTime? updatedAt;
  final String? imageBase64;
}
