import 'package:flutter/foundation.dart';

const privacyPolicyUrl = String.fromEnvironment(
  'PRIVACY_POLICY_URL',
  defaultValue: '',
);

/// Falla temprano si un artefacto oficial omite su política de privacidad.
void validateReleaseConfiguration() {
  if (!kReleaseMode) return;
  final uri = Uri.tryParse(privacyPolicyUrl);
  if (uri == null || uri.scheme != 'https' || uri.host.isEmpty) {
    throw StateError(
      'PRIVACY_POLICY_URL debe ser una URL HTTPS válida en release.',
    );
  }
}
