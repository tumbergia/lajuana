const _monthAbbreviations = [
  'ene',
  'feb',
  'mar',
  'abr',
  'may',
  'jun',
  'jul',
  'ago',
  'sep',
  'oct',
  'nov',
  'dic',
];

String _normalizeIsoDate(String raw) {
  if (raw.contains('T')) return raw.split('T').first;
  if (raw.contains(' ')) return raw.split(' ').first;
  return raw;
}

DateTime? _tryParseVoiceDate(String? raw) {
  if (raw == null || raw.trim().isEmpty) return null;
  final normalized = _normalizeIsoDate(raw.trim());
  return DateTime.tryParse(normalized);
}

/// Fecha legible para respuestas del asistente (ej. `5 jul 2026`).
String formatVoiceDate(String? raw) {
  final date = _tryParseVoiceDate(raw);
  if (date == null) {
    return raw?.trim().isNotEmpty == true ? raw!.trim() : 'Sin fecha';
  }
  return '${date.day} ${_monthAbbreviations[date.month - 1]} ${date.year}';
}

/// Fecha y hora legibles (ej. `5 jul 2026 · 14:30`).
String formatVoiceDateTime(String? raw) {
  if (raw == null || raw.trim().isEmpty) return 'Sin fecha';
  final parsed = DateTime.tryParse(raw.trim());
  if (parsed == null) return formatVoiceDate(raw);
  final datePart = formatVoiceDate(raw);
  final hour = parsed.hour.toString().padLeft(2, '0');
  final minute = parsed.minute.toString().padLeft(2, '0');
  return '$datePart · $hour:$minute';
}

/// Hora corta (`14:30`) desde ISO o `HH:MM`.
String formatVoiceTime(String? raw) {
  if (raw == null || raw.trim().isEmpty) return '';
  final trimmed = raw.trim();
  if (RegExp(r'^\d{2}:\d{2}').hasMatch(trimmed)) {
    return trimmed.substring(0, 5);
  }
  final parsed = DateTime.tryParse(trimmed);
  if (parsed == null) return trimmed;
  final hour = parsed.hour.toString().padLeft(2, '0');
  final minute = parsed.minute.toString().padLeft(2, '0');
  return '$hour:$minute';
}
