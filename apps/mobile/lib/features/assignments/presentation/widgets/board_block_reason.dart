/// Motivos de bloqueo redundantes en la sección "no disponibles".
///
/// Ya están implícitos por el contexto (sección, estado visual) o no aportan detalle.
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

  return trimmed;
}
