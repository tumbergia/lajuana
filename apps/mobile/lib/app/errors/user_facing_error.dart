/// Normalizes exceptions / API failures into a short Spanish message for UI.
///
/// Never returns raw [Object.toString] values such as `Exception: ...` or
/// `FooApiFailure(code): ...`. Prefer the typed `message` when it looks human.
String userFacingError(
  Object error, {
  required String fallback,
}) {
  final isTypedFailure = _isTypedApiFailure(error);
  final message = _extractMessage(error);
  final code = _extractCode(error);

  if (isTypedFailure) {
    if (message != null) {
      final trimmed = message.trim();
      if (trimmed.isNotEmpty && !_looksTechnical(trimmed)) {
        return trimmed;
      }
    }
    if (code != null) {
      final mapped = _mapCommonCode(code);
      if (mapped != null) return mapped;
    }
    return fallback;
  }

  // Untyped Exception / Error / random objects → never leak toString().
  return fallback;
}

bool _isTypedApiFailure(Object error) {
  final name = error.runtimeType.toString();
  return name.contains('ApiFailure') || name == 'AuthFailure';
}

String? _extractMessage(Object error) {
  try {
    final dynamic value = (error as dynamic).message;
    if (value is String) return value;
  } catch (_) {
    // Not every exception exposes `message`.
  }
  return null;
}

String? _extractCode(Object error) {
  try {
    final dynamic value = (error as dynamic).code;
    if (value is String) return value;
  } catch (_) {
    // Not every exception exposes `code`.
  }
  return null;
}

String? _mapCommonCode(String code) {
  final normalized = code.trim().toLowerCase();
  if (normalized.isEmpty) return null;

  if (normalized.contains('forbidden') ||
      normalized.contains('permission') ||
      normalized == 'auth.forbidden') {
    return 'No tienes permiso para esta acción.';
  }
  if (normalized.contains('unauthorized') ||
      normalized.contains('unauthenticated') ||
      normalized == 'auth.unauthorized') {
    return 'Tu sesión expiró. Vuelve a iniciar sesión.';
  }
  if (normalized.contains('not_found') || normalized.endsWith('.not_found')) {
    return 'No encontramos lo que buscabas.';
  }
  if (normalized.contains('validation') ||
      normalized == 'common.validation_error') {
    return 'Revisa los datos e inténtalo de nuevo.';
  }
  if (normalized.contains('timeout') ||
      normalized.contains('unavailable') ||
      normalized.contains('unreachable') ||
      normalized.startsWith('network.')) {
    return 'El servicio no respondió a tiempo. Intenta nuevamente.';
  }
  return null;
}

bool _looksTechnical(String message) {
  final trimmed = message.trim();
  final lower = trimmed.toLowerCase();

  if (RegExp(r'^\w+ApiFailure\(', caseSensitive: false).hasMatch(trimmed)) {
    return true;
  }
  if (trimmed.startsWith('Exception:') ||
      trimmed.startsWith('Error:') ||
      lower.startsWith('exception:')) {
    return true;
  }
  if (lower.contains('socketexception') ||
      lower.contains('timeoutexception') ||
      lower.contains('handshakeexception') ||
      lower.contains('clientexception') ||
      lower.contains('formatexception') ||
      lower.contains('typeerror') ||
      lower.contains('null check operator') ||
      lower.contains('stack trace') ||
      lower.contains('dart:')) {
    return true;
  }
  // Bare error codes like `role_request.not_pending`.
  if (!trimmed.contains(' ') &&
      RegExp(r'^[a-z][a-z0-9_]*\.[a-z0-9_.]+$', caseSensitive: false)
          .hasMatch(trimmed)) {
    return true;
  }
  return false;
}
