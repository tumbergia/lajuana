import 'dart:ui' show VoidCallback;

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/cards/app_logbook_timeline.dart';
import 'package:mobile_domain/src/equines/equine.dart';
import 'package:mobile_domain/src/equines/equine_operational_status.dart';
import 'package:mobile_domain/src/equines/equine_event.dart';
import 'package:mobile_domain/src/equines/equine_timeline_entry.dart';
import 'package:mobile_domain/src/gen/equine.dart' as gen;
import 'package:mobile/features/equines/presentation/models/equine_view_models.dart';
import 'package:mobile/features/equines/presentation/equine_event_labels.dart';
import 'package:mobile/features/equines/infrastructure/remote/equine_dtos.dart';

/// Mapea EquineDto del backend  →  Equine del dominio  →  ViewModel para UI.
class EquineMapper {
  /// Convierte [EquineDto] → [Equine] de dominio delegando en [gen.Equine].
  ///
  /// Usa [EquineDto.toJson] para generar JSON compatible con [gen.Equine.fromJson],
  /// luego [Equine.fromGen] para la conversión final. Esto elimina la duplicación
  /// manual de campo por campo y unifica la fuente de verdad en el modelo generado.
  static Equine dtoToDomain(EquineDto dto) {
    final json = dto.toJson();
    // Asegurar fechas no vacías para gen.Equine.fromJson (DateTime.parse).
    if (json['created_at'] is String && (json['created_at'] as String).isEmpty) {
      json['created_at'] = '1970-01-01T00:00:00Z';
    }
    if (json['updated_at'] is String && (json['updated_at'] as String).isEmpty) {
      json['updated_at'] = '1970-01-01T00:00:00Z';
    }
    // Sanitizar operational_status: el gen model lanza excepción para valores
    // desconocidos; el manual EquineOperationalStatus.fromApi() fallback a
    // unavailable. Igualamos ese comportamiento.
    final opStatus = json['operational_status'] as String?;
    if (opStatus == null || !_validOpStatuses.contains(opStatus)) {
      json['operational_status'] = 'unavailable';
    }
    return Equine.fromGen(gen.Equine.fromJson(Map<String, dynamic>.from(json)));
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
      updatedAt: equine.updatedAt,
    );
  }

  static EquineTimelineEntry timelineEntryDtoToDomain(EquineTimelineEntryDto dto) {
    // Si la fecha no se puede parsear, usar epoch como centinela.
    // La UI ocultará entradas con happenedAt en 1970.
    final happenedAt =
        DateTime.tryParse(dto.happenedAt)?.toUtc() ?? DateTime.utc(1970);
    return EquineTimelineEntry(
      id: dto.id,
      source: dto.source,
      eventType: dto.eventType,
      happenedAt: happenedAt,
      title: dto.title,
      reservationId: dto.reservationId,
      notes: dto.notes,
      severity: dto.severity,
      affectsAvailability: dto.affectsAvailability,
      measuredWeightKg: dto.measuredWeightKg,
      measuredHeightM: dto.measuredHeightM,
      nextDueAt: DateTime.tryParse(dto.nextDueAt ?? '')?.toUtc(),
      performedBy: dto.performedBy,
      medicationName: dto.medicationName,
      dosage: dto.dosage,
      labResultSummary: dto.labResultSummary,
      resultingOperationalStatus: dto.resultingOperationalStatus,
      restUntil: DateTime.tryParse(dto.restUntil ?? '')?.toUtc(),
    );
  }

  static EquineTimelineEntry eventToTimelineEntry(EquineEvent event) {
    return EquineTimelineEntry(
      id: event.id,
      source: 'equine_event',
      eventType: event.eventType,
      happenedAt: event.happenedAt,
      title: event.title,
      notes: event.description,
      severity: event.severity,
      affectsAvailability: event.affectsAvailability,
      syncPending: event.syncPending,
      measuredWeightKg: event.measuredWeightKg,
      nextDueAt: event.nextDueAt,
      performedBy: event.performedBy,
      resultingOperationalStatus: event.resultingOperationalStatus,
      restUntil: event.restUntil,
    );
  }

  static AppLogbookTimelineEntry timelineEntryToLogbookEntry(
    EquineTimelineEntry entry, {
    VoidCallback? onTap,
  }) {
    final isCare = entry.source == 'equine_event';

    // Badge con el tipo de evento (o "Pendiente" si aún no sincronizó).
    final badge = AppBadge(
      label: entry.syncPending
          ? 'Pendiente'
          : equineEventTypeLabel(entry.eventType),
      tone: entry.syncPending
          ? AppBadgeTone.warning
          : _badgeToneFromState(_logbookStateFromEntry(entry)),
      uppercase: false,
    );

    // Detalle estructurado: profundiza la bitácora mostrando cada dato del
    // evento de cuidado sin necesidad de abrirlo.
    final details = <AppLogbookDetail>[
      AppLogbookDetail(label: 'Tipo', value: equineEventTypeLabel(entry.eventType)),
      if (entry.severity != null)
        AppLogbookDetail(
          label: 'Severidad',
          value: equineEventSeverityLabel(entry.severity!),
        ),
      if (entry.performedBy != null && entry.performedBy!.isNotEmpty)
        AppLogbookDetail(label: 'Realizado por', value: entry.performedBy!),
      if (entry.measuredWeightKg != null)
        AppLogbookDetail(
          label: 'Peso',
          value: '${_formatDecimal(entry.measuredWeightKg!)} kg',
        ),
      if (entry.measuredHeightM != null)
        AppLogbookDetail(
          label: 'Altura',
          value: '${_formatDecimal(entry.measuredHeightM!)} m',
        ),
      if (entry.nextDueAt != null)
        AppLogbookDetail(
          label: 'Próximo control',
          value: _formatDateShort(entry.nextDueAt!.toLocal()),
        ),
      if (entry.resultingOperationalStatus != null)
        AppLogbookDetail(
          label: 'Estado resultante',
          value: _statusLabel(
            EquineOperationalStatus.fromApi(entry.resultingOperationalStatus!),
          ),
        ),
      if (entry.restUntil != null)
        AppLogbookDetail(
          label: 'Reposo hasta',
          value: _formatDateShort(entry.restUntil!.toLocal()),
        ),
      if (entry.affectsAvailability)
        const AppLogbookDetail(
          label: 'Disponibilidad',
          value: 'Afecta disponibilidad',
        ),
      if (entry.medicationName != null && entry.medicationName!.isNotEmpty)
        AppLogbookDetail(
          label: 'Medicación',
          value: entry.dosage != null && entry.dosage!.isNotEmpty
              ? '${entry.medicationName} · ${entry.dosage}'
              : entry.medicationName!,
          fullWidth: true,
        ),
      if (entry.labResultSummary != null && entry.labResultSummary!.isNotEmpty)
        AppLogbookDetail(
          label: 'Resultado',
          value: entry.labResultSummary!,
          fullWidth: true,
        ),
      if (!isCare && entry.reservationId != null)
        AppLogbookDetail(label: 'Reserva', value: entry.reservationId!),
    ];

    return AppLogbookTimelineEntry(
      title: entry.title,
      dateLabel: _formatDateTimeShort(entry.happenedAt.toLocal()),
      details: details,
      badge: badge,
      state: _logbookStateFromEntry(entry),
      observations: (entry.notes != null && entry.notes!.isNotEmpty)
          ? entry.notes
          : null,
      onTap: onTap,
    );
  }

  static AppBadgeTone _badgeToneFromState(AppLogbookEntryState state) {
    switch (state) {
      case AppLogbookEntryState.active:
        return AppBadgeTone.primary;
      case AppLogbookEntryState.completed:
        return AppBadgeTone.success;
      case AppLogbookEntryState.warning:
        return AppBadgeTone.warning;
      case AppLogbookEntryState.error:
        return AppBadgeTone.danger;
      case AppLogbookEntryState.neutral:
        return AppBadgeTone.neutral;
    }
  }

  static AppLogbookEntryState _logbookStateFromEntry(EquineTimelineEntry entry) {
    if (entry.syncPending) return AppLogbookEntryState.warning;
    if (entry.affectsAvailability) return AppLogbookEntryState.warning;
    return _logbookStateFromEventType(entry.eventType, entry.severity);
  }

  static AppLogbookEntryState _logbookStateFromEventType(
    String eventType, [
    String? severity,
  ]) {
    switch (eventType) {
      case 'arrival':
      case 'departure':
      case 'closure':
        return AppLogbookEntryState.completed;
      case 'checkpoint':
        return AppLogbookEntryState.active;
      case 'incident':
      case 'injury':
        return AppLogbookEntryState.warning;
      case 'treatment':
      case 'medication':
      case 'rest':
        return severity == 'high' || severity == 'critical'
            ? AppLogbookEntryState.warning
            : AppLogbookEntryState.neutral;
      case 'vaccination':
      case 'farrier':
      case 'weight':
      case 'health_check':
        return AppLogbookEntryState.completed;
      case 'note':
        return AppLogbookEntryState.neutral;
      default:
        return AppLogbookEntryState.neutral;
    }
  }

  static String _formatDateShort(DateTime dt) {
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
  }

  static String _formatDateTimeShort(DateTime dt) {
    final hh = dt.hour.toString().padLeft(2, '0');
    final mm = dt.minute.toString().padLeft(2, '0');
    return '${_formatDateShort(dt)} · $hh:$mm';
  }

  /// Formatea un decimal sin ceros sobrantes (420.0 → "420", 3.50 → "3.5").
  static String _formatDecimal(double value) {
    if (value == value.roundToDouble()) {
      return value.toStringAsFixed(0);
    }
    return value
        .toStringAsFixed(2)
        .replaceFirst(RegExp(r'0+$'), '')
        .replaceFirst(RegExp(r'\.$'), '');
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

// ── Helpers privados (top-level, accesibles desde EquineMapper) ──
// Convención: file-private para mantener el mapper autocontenido.

/// Valores de operational_status aceptados por el gen model.
const _validOpStatuses = {
  'available', 'resting', 'in_service', 'injured', 'retired',
  'unavailable', 'restricted',
};

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
  final reasons = equine.availabilityReasons;
  if (reasons != null && reasons.isNotEmpty && !reasons.contains('=')) {
    return reasons;
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

/// Normaliza availabilityReasons técnicos (ej. "status=restricted")
/// a texto legible en español. Si no reconoce el patrón, devuelve el original.
String normalizeReason(String reason) {
  if (reason.contains('=')) {
    final parts = reason.split(';');
    for (final part in parts) {
      final trimmed = part.trim();
      if (trimmed.startsWith('status=')) {
        final status = trimmed.substring(7);
        switch (status) {
          case 'restricted':
            return 'Acceso restringido';
          case 'active':
            return 'Disponible';
        }
      }
      if (trimmed.startsWith('is_assignable=false')) {
        return 'No asignable a participantes';
      }
    }
  }
  return reason;
}
