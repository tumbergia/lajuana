/// Lightweight submit-time input helpers (no UI).
abstract final class InputValidation {
  static final RegExp _emailPattern = RegExp(
    r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
  );

  static bool isValidEmail(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return false;
    return _emailPattern.hasMatch(trimmed);
  }

  /// Optional email: empty is valid; non-empty must look like an email.
  static bool isValidOptionalEmail(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return true;
    return isValidEmail(trimmed);
  }

  static bool isValidHttpUrl(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return false;
    final uri = Uri.tryParse(trimmed);
    if (uri == null || !uri.hasScheme || uri.host.isEmpty) return false;
    final scheme = uri.scheme.toLowerCase();
    return scheme == 'http' || scheme == 'https';
  }

  static double? parseDecimal(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    return double.tryParse(trimmed.replaceAll(',', '.'));
  }

  static int? parseInteger(String value) {
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    return int.tryParse(trimmed);
  }
}
