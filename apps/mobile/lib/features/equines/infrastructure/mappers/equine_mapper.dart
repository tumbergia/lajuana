import '../../../../app/widgets/app_badge.dart';
import '../../domain/models/equine.dart';
import '../../domain/models/equine_experience_fit.dart';
import '../../domain/models/equine_operational_status.dart';
import '../../presentation/models/equine_view_models.dart';
import '../remote/equine_dtos.dart';

/// Mapea EquineDto del backend  →  Equine del dominio  →  ViewModel para UI.
class EquineMapper {
  static Equine dtoToDomain(EquineDto dto) {
    return Equine(
      id: dto.id,
      name: dto.name,
      inventoryNumber: dto.inventoryNumber,
      species: dto.species,
      locationStatus: dto.locationStatus,
      locationNotes: dto.locationNotes,
      breed: dto.breed,
      sex: dto.sex,
      coatColor: dto.coatColor,
      gait: dto.gait,
      approximateBirthDate: dto.approximateBirthDate,
      approximateAgeYears: dto.approximateAgeYears,
      birthDateIsApproximate: dto.birthDateIsApproximate,
      birthDateRaw: dto.birthDateRaw,
      birthPlace: dto.birthPlace,
      registryNumber: dto.registryNumber,
      microchip: dto.microchip,
      sireName: dto.sireName,
      damName: dto.damName,
      weightKg: dto.weightKg,
      heightM: dto.heightM,
      lastWeightAt: dto.lastWeightAt,
      lastHeightAt: dto.lastHeightAt,
      isActive: dto.isActive,
      isAvailable: dto.isAvailable,
      operationalStatus:
          EquineOperationalStatus.fromApi(dto.operationalStatus),
      availabilityNotes: dto.availabilityNotes,
      availabilityReasons: dto.availabilityReasons,
      restUntil: dto.restUntil != null
          ? DateTime.tryParse(dto.restUntil!)?.toUtc()
          : null,
      maxRiderWeightKg: dto.maxRiderWeightKg,
      experienceFit: dto.experienceFit != null
          ? EquineExperienceFit.fromApi(dto.experienceFit!)
          : null,
      lastServiceAt: dto.lastServiceAt != null
          ? DateTime.tryParse(dto.lastServiceAt!)?.toUtc()
          : null,
      workloadLast7Days: dto.workloadLast7Days,
      imageBase64: dto.imageBase64,
      sourceFile: dto.sourceFile,
    );
  }

  static EquineRecord domainToRecord(Equine equine) {
    return EquineRecord(
      id: equine.id,
      name: equine.name,
      inventoryNumber: equine.inventoryNumber,
      species: equine.species,
      breed: equine.breed,
      sex: equine.sex,
      statusLabel: _statusLabel(equine.operationalStatus),
      statusTone: _statusTone(equine.operationalStatus),
      summary: _summary(equine),
      subtitle: _subtitle(equine),
      isAvailable: equine.isAvailable,
      weightKg: equine.weightKg,
      imageBase64: equine.imageBase64,
    );
  }

  static EquineDetailRecord domainToDetailRecord(Equine equine) {
    return EquineDetailRecord(
      id: equine.id,
      name: equine.name,
      inventoryNumber: equine.inventoryNumber,
      species: equine.species,
      locationStatus: equine.locationStatus,
      locationNotes: equine.locationNotes,
      breed: equine.breed,
      sex: equine.sex,
      coatColor: equine.coatColor,
      gait: equine.gait,
      approximateBirthDate: equine.approximateBirthDate,
      approximateAgeYears: equine.approximateAgeYears,
      birthDateIsApproximate: equine.birthDateIsApproximate,
      birthDateRaw: equine.birthDateRaw,
      birthPlace: equine.birthPlace,
      registryNumber: equine.registryNumber,
      microchip: equine.microchip,
      sireName: equine.sireName,
      damName: equine.damName,
      weightKg: equine.weightKg,
      heightM: equine.heightM,
      lastWeightAt: equine.lastWeightAt,
      lastHeightAt: equine.lastHeightAt,
      isActive: equine.isActive,
      isAvailable: equine.isAvailable,
      operationalStatus: equine.operationalStatus,
      statusLabel: _statusLabel(equine.operationalStatus),
      statusTone: _statusTone(equine.operationalStatus),
      availabilityNotes: equine.availabilityNotes,
      availabilityReasons: equine.availabilityReasons,
      restUntil: equine.restUntil,
      maxRiderWeightKg: equine.maxRiderWeightKg,
      experienceFit: equine.experienceFit,
      lastServiceAt: equine.lastServiceAt,
      workloadLast7Days: equine.workloadLast7Days,
      imageBase64: equine.imageBase64,
      updatedAt: equine.lastServiceAt,
    );
  }

  static String _statusLabel(EquineOperationalStatus status) {
    switch (status) {
      case EquineOperationalStatus.available:
        return 'Disponible';
      case EquineOperationalStatus.resting:
        return 'Descanso';
      case EquineOperationalStatus.inService:
        return 'En servicio';
      case EquineOperationalStatus.injured:
        return 'Lesionado';
      case EquineOperationalStatus.retired:
        return 'Retirado';
      case EquineOperationalStatus.unavailable:
        return 'No disponible';
      case EquineOperationalStatus.restricted:
        return 'Restringido';
    }
  }
}

AppBadgeTone _statusTone(EquineOperationalStatus status) {
  switch (status) {
    case EquineOperationalStatus.available:
      return AppBadgeTone.success;
    case EquineOperationalStatus.resting:
      return AppBadgeTone.neutral;
    case EquineOperationalStatus.inService:
      return AppBadgeTone.primary;
    case EquineOperationalStatus.injured:
      return AppBadgeTone.warning;
    case EquineOperationalStatus.retired:
      return AppBadgeTone.danger;
    case EquineOperationalStatus.unavailable:
      return AppBadgeTone.danger;
    case EquineOperationalStatus.restricted:
      return AppBadgeTone.warning;
  }
}

String _summary(Equine equine) {
  if (equine.availabilityReasons != null &&
      equine.availabilityReasons!.isNotEmpty) {
    return equine.availabilityReasons!;
  }
  switch (equine.operationalStatus) {
    case EquineOperationalStatus.available:
      return 'Disponible para asignación';
    case EquineOperationalStatus.resting:
      if (equine.restUntil != null) {
        return 'Descanso hasta ${_formatDate(equine.restUntil!)}';
      }
      return 'En descanso';
    case EquineOperationalStatus.inService:
      return 'En servicio actualmente';
    case EquineOperationalStatus.injured:
      return 'En observación veterinaria';
    case EquineOperationalStatus.retired:
      return 'Dado de baja operativa';
    case EquineOperationalStatus.unavailable:
      return 'No disponible temporalmente';
    case EquineOperationalStatus.restricted:
      return 'Acceso restringido';
  }
}

String _subtitle(Equine equine) {
  final parts = <String>[];
  if (equine.species != 'unknown') {
    parts.add(_speciesLabel(equine.species));
  }
  if (equine.breed != null && equine.breed!.isNotEmpty) {
    parts.add(equine.breed!);
  }
  if (equine.approximateAgeYears != null) {
    parts.add('${equine.approximateAgeYears} años');
  }
  if (equine.sex != 'unknown') {
    parts.add(equine.sex == 'male' ? 'Macho' : 'Hembra');
  }
  return parts.isNotEmpty ? parts.join(' · ') : '';
}

String _speciesLabel(String species) {
  switch (species) {
    case 'mule':
      return 'Mula';
    case 'donkey':
      return 'Asno';
    case 'horse':
      return 'Caballo';
    default:
      return '';
  }
}

String _formatDate(DateTime date) {
  final day = date.day.toString().padLeft(2, '0');
  final month = date.month.toString().padLeft(2, '0');
  return '$day/$month';
}
