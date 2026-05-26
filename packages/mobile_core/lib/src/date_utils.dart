const _months = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
];

/// Normalizes a date string to Spanish long format: "20 de mayo de 2026".
///
/// Accepts ISO date strings like:
///   - `"2026-05-30"` (date-only)
///   - `"2026-05-20T21:18:30.748000"` (ISO datetime)
///
/// Returns [fallback] when [dateString] is null, empty, or unparseable.
///
/// Example:
/// ```dart
/// formatDate('2026-05-20') // → "20 de mayo de 2026"
/// formatDate(null)          // → "Sin fecha"
/// formatDate('', fallback: '') // → ""
/// ```
String formatDate(String? dateString, {String fallback = 'Sin fecha'}) {
  if (dateString == null || dateString.isEmpty) return fallback;
  final date = DateTime.tryParse(dateString);
  if (date == null) return fallback;
  return '${date.day} de ${_months[date.month - 1]} de ${date.year}';
}
