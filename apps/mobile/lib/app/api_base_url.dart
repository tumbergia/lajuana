import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/foundation.dart';

/// Garantiza esquema HTTP(S) para [Uri.parse] (p. ej. `localhost:8000` → `http://...`).
String normalizeApiBaseUrl(String raw) {
  final trimmed = raw.trim();
  if (trimmed.isEmpty) return trimmed;
  final lower = trimmed.toLowerCase();
  if (lower.startsWith('http://') || lower.startsWith('https://')) {
    return trimmed;
  }
  return 'http://$trimmed';
}

/// Resuelve la URL base del API para desarrollo local.
///
/// Prioridad: [API_BASE_URL] (`--dart-define`) > heurística por plataforma.
Future<String> resolveApiBaseUrl() async {
  const env = String.fromEnvironment('API_BASE_URL', defaultValue: '');
  if (env.isNotEmpty) {
    if (kIsWeb && _isWebUnsafeHost(env)) {
      debugPrint(
        'Ignorando API_BASE_URL=$env en web. Usa localhost/127.0.0.1.',
      );
    } else {
      final url = normalizeApiBaseUrl(env);
      await _warnAndroidPhysicalLoopback(url);
      return url;
    }
  }

  if (kIsWeb) {
    return 'http://localhost:8000/api/v1';
  }

  if (defaultTargetPlatform == TargetPlatform.android) {
    final android = await DeviceInfoPlugin().androidInfo;
    if (!android.isPhysicalDevice) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    const url = 'http://127.0.0.1:8000/api/v1';
    await _warnAndroidPhysicalLoopback(url);
    return url;
  }

  return 'http://127.0.0.1:8000/api/v1';
}

Future<void> _warnAndroidPhysicalLoopback(String url) async {
  if (defaultTargetPlatform != TargetPlatform.android) return;
  final android = await DeviceInfoPlugin().androidInfo;
  if (!android.isPhysicalDevice) return;
  final uri = Uri.tryParse(url);
  final host = uri?.host.toLowerCase() ?? '';
  if (host != '127.0.0.1' && host != 'localhost') return;
  debugPrint(
    'API: Android físico con $url — 127.0.0.1/localhost es el TELÉFONO, no tu PC. '
    'USB: adb reverse tcp:8000 tcp:8000. '
    'Wi‑Fi: MOBILE_API_BASE_URL=http://<IP-LAN-de-tu-PC>:8000/api/v1 make mobile-profile '
    'y arranca el API con --host 0.0.0.0.',
  );
}

bool _isWebUnsafeHost(String url) {
  final host = Uri.tryParse(url)?.host.toLowerCase();
  return host == '10.0.2.2' || host == '127.0.0.1.nip.io';
}
