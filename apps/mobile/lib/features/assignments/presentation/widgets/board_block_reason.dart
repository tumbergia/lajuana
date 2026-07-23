import 'package:mobile/features/equines/presentation/equine_labels.dart';
import 'package:mobile_domain/src/equines/equine_operational_status.dart';

/// Motivos de bloqueo redundantes en la sección "no disponibles".
///
/// Ya quedan implícitos por el contexto (sección, estado visual) o no aportan detalle.
String? displayBoardBlockReason(String? reason) {
  if (reason == null) return null;

  final trimmed = reason.trim();
  if (trimmed.isEmpty) return null;

  final lower = trimmed.toLowerCase();

  if (lower.startsWith('ya asignad')) return null;
  if (lower.contains('eliminad')) return null;
  if (lower == 'equino no disponible' || lower == 'silla no disponible') {
    return null;
  }
  if (lower == 'equino inactivo' || lower == 'silla inactiva') return null;

  final operationalMatch = RegExp(
    r'^estado operativo:\s*(.+)$',
    caseSensitive: false,
  ).firstMatch(trimmed);
  if (operationalMatch != null) {
    final token = operationalMatch.group(1)!.trim().toLowerCase();
    final status = _parseOperationalStatus(token);
    if (status != null) {
      return 'Estado operativo: ${equineStatusLabel(status)}';
    }
  }

  return trimmed;
}

EquineOperationalStatus? _parseOperationalStatus(String token) {
  return switch (token) {
    'available' => EquineOperationalStatus.available,
    'resting' => EquineOperationalStatus.resting,
    'in_service' => EquineOperationalStatus.inService,
    'injured' => EquineOperationalStatus.injured,
    'retired' => EquineOperationalStatus.retired,
    'unavailable' => EquineOperationalStatus.unavailable,
    'restricted' => EquineOperationalStatus.restricted,
    _ => null,
  };
}
