/// Safely parse an [Object?] to [int]?.
///
/// Handles:
/// - `null` → `null`
/// - `int` → value
/// - `double` → truncated via `toInt()`
/// - `String` → `int.tryParse` (after trim)
/// - `bool` → `true` → 1, `false` → 0
/// - other → `null`
int? parseInt(Object? value) {
  if (value == null) return null;
  if (value is int) return value;
  if (value is double) return value.toInt();
  if (value is bool) return value ? 1 : 0;
  if (value is String) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    return int.tryParse(trimmed);
  }
  return null;
}

/// Safely parse an [Object?] to [double]?.
///
/// Handles:
/// - `null` → `null`
/// - `num` (int/double) → `toDouble()`
/// - `String` → `double.tryParse` (after trim)
/// - `bool` → `true` → 1.0, `false` → 0.0
/// - other → `null`
double? parseDouble(Object? value) {
  if (value == null) return null;
  if (value is num) return value.toDouble();
  if (value is bool) return value ? 1.0 : 0.0;
  if (value is String) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    return double.tryParse(trimmed);
  }
  return null;
}

/// Safely parse an [Object?] to [num]?.
///
/// Delegates to [parseDouble] and keeps the result as [num]?.
num? parseNum(Object? value) => parseDouble(value);
