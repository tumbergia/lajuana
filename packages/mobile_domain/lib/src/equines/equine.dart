import 'equine_experience_fit.dart';
import 'equine_operational_status.dart';
import '../gen/equine.dart' as gen;

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

  /// Crea un [Equine] de dominio desde el modelo generado [gen.Equine].
  /// Convierte tipos: String→int?, String→double?, String→DateTime?, enum→String.
  factory Equine.fromGen(gen.Equine source) {
    return Equine(
      id: source.id,
      name: source.name,
      inventoryNumber: int.tryParse(source.inventoryNumber),
      species: source.species.value,
      locationStatus: source.locationStatus.value,
      locationNotes: source.locationNotes.isNotEmpty ? source.locationNotes : null,
      breed: source.breed.isNotEmpty ? source.breed : null,
      sex: source.sex.value,
      coatColor: source.coatColor.isNotEmpty ? source.coatColor : null,
      gait: source.gait.isNotEmpty ? source.gait : null,
      approximateBirthDate: source.approximateBirthDate.isNotEmpty
          ? source.approximateBirthDate
          : null,
      approximateAgeYears: int.tryParse(source.approximateAgeYears),
      birthDateIsApproximate: source.birthDateIsApproximate,
      birthDateRaw: source.birthDateRaw.isNotEmpty ? source.birthDateRaw : null,
      birthPlace: source.birthPlace.isNotEmpty ? source.birthPlace : null,
      registryNumber: source.registryNumber.isNotEmpty ? source.registryNumber : null,
      microchip: source.microchip.isNotEmpty ? source.microchip : null,
      sireName: source.sireName.isNotEmpty ? source.sireName : null,
      damName: source.damName.isNotEmpty ? source.damName : null,
      weightKg: double.tryParse(source.weightKg),
      heightM: double.tryParse(source.heightM),
      lastWeightAt: source.lastWeightAt.isNotEmpty ? source.lastWeightAt : null,
      lastHeightAt: source.lastHeightAt.isNotEmpty ? source.lastHeightAt : null,
      isActive: source.isActive,
      isAvailable: source.isAvailable,
      operationalStatus:
          EquineOperationalStatus.fromApi(source.operationalStatus.value),
      availabilityNotes:
          source.availabilityNotes.isNotEmpty ? source.availabilityNotes : null,
      availabilityReasons:
          source.availabilityReasons.isNotEmpty ? source.availabilityReasons : null,
      restUntil: source.restUntil.isNotEmpty
          ? DateTime.tryParse(source.restUntil)
          : null,
      maxRiderWeightKg: double.tryParse(source.maxRiderWeightKg),
      experienceFit: source.experienceFit.isNotEmpty
          ? EquineExperienceFit.fromApi(source.experienceFit)
          : null,
      lastServiceAt: source.lastServiceAt != null
          ? DateTime.tryParse(source.lastServiceAt!)
          : null,
      workloadLast7Days: source.workloadLast7Days,
      sourceFile: source.sourceFile.isNotEmpty ? source.sourceFile : null,
      imageBase64: source.imageBase64,
      updatedAt: source.updatedAt,
    );
  }

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
