import 'equine_experience_fit.dart';
import 'equine_operational_status.dart';

/// Modelo de dominio completo para un equino (CV real).
class Equine {
  const Equine({
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
    this.operationalStatus = EquineOperationalStatus.available,
    this.availabilityNotes,
    this.availabilityReasons,
    this.restUntil,
    this.maxRiderWeightKg,
    this.experienceFit,
    this.lastServiceAt,
    this.workloadLast7Days = 0,
    this.sourceFile,
    this.imageBase64,
    this.updatedAt,
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
  final String? availabilityNotes;
  final String? availabilityReasons;
  final DateTime? restUntil;
  final double? maxRiderWeightKg;
  final EquineExperienceFit? experienceFit;
  final DateTime? lastServiceAt;
  final int workloadLast7Days;
  final String? sourceFile;
  final String? imageBase64;
  final DateTime? updatedAt;
}
