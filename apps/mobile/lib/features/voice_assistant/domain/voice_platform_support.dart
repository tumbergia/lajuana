import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;

/// Capacidades de voz según plataforma.
abstract final class VoicePlatformSupport {
  static bool get isLinux {
    if (kIsWeb) return false;
    return defaultTargetPlatform == TargetPlatform.linux;
  }

  static bool get isDesktopLike {
    if (kIsWeb) return false;
    return defaultTargetPlatform == TargetPlatform.linux ||
        defaultTargetPlatform == TargetPlatform.macOS ||
        defaultTargetPlatform == TargetPlatform.windows;
  }

  /// STT nativo via speech_to_text (Linux no tiene soporte de speech).
  static bool get supportsNativeSpeech {
    if (kIsWeb) return true;
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
      case TargetPlatform.windows:
        return true;
      case TargetPlatform.linux:
      case TargetPlatform.fuchsia:
        return false;
    }
  }

  /// Pull-to-voice con puntero (ratón/trackpad) además del overscroll.
  static bool get prefersPointerVoicePull => kIsWeb || isDesktopLike;

  /// En web el permiso de micrófono requiere un gesto explícito del usuario.
  static bool get requiresExplicitListenGesture => kIsWeb;

  static String get unsupportedSpeechHint {
    if (isLinux) {
      return 'En Linux escribe el comando abajo. El reconocimiento de voz no está disponible en este sistema.';
    }
    if (kIsWeb) {
      return 'Si el micrófono no responde, escribe el comando abajo. Usa Chrome o Edge en localhost/HTTPS.';
    }
    return 'Escribe el comando abajo o usa el micrófono.';
  }
}
