import 'package:flutter/material.dart';

abstract final class AppColors {
  static const Color success = Color(0xFF2E7D32);
  static const Color warning = Color(0xFFF9A825);
  static const Color danger = Color(0xFFB3261E);

  static const ColorScheme darkColorScheme = ColorScheme(
    brightness: Brightness.dark,
    primary: Color(0xFFFFFFFF),
    onPrimary: Color(0xFF1A1C1C),
    primaryContainer: Color(0xFFD4D4D4),
    onPrimaryContainer: Color(0xFF000000),

    secondary: Color(0xFFC7C6C6),
    onSecondary: Color(0xFF1A1C1C),
    secondaryContainer: Color(0xFF464747),
    onSecondaryContainer: Color(0xFFE3E2E2),

    tertiary: Color(0xFFE2E2E2),
    onTertiary: Color(0xFF1B1B1B),
    tertiaryContainer: Color(0xFF919191),
    onTertiaryContainer: Color(0xFF000000),

    error: Color(0xFFFFB4AB),
    onError: Color(0xFF690005),
    errorContainer: Color(0xFF93000A),
    onErrorContainer: Color(0xFFFFDAD6),

    surface: Color(0xFF131313),
    onSurface: Color(0xFFE2E2E2),
    surfaceContainerLowest: Color(0xFF0E0E0E),
    surfaceContainerLow: Color(0xFF1B1B1B),
    surfaceContainer: Color(0xFF1F1F1F),
    surfaceContainerHigh: Color(0xFF2A2A2A),
    surfaceContainerHighest: Color(0xFF353535),

    onSurfaceVariant: Color(0xFFC6C6C6),
    outline: Color(0xFF919191),
    outlineVariant: Color(0xFF474747),

    shadow: Color(0xFF000000),
    scrim: Color(0xFF000000),

    inverseSurface: Color(0xFFE2E2E2),
    onInverseSurface: Color(0xFF303030),
    inversePrimary: Color(0xFF5D5F5F),

    surfaceTint: Color(0xFFC6C6C7),
  );

  static const ColorScheme lightColorScheme = ColorScheme(
    brightness: Brightness.light,
    primary: Color(0xFF1A1C1C),
    onPrimary: Color(0xFFFFFFFF),
    primaryContainer: Color(0xFFD4D4D4),
    onPrimaryContainer: Color(0xFF000000),

    secondary: Color(0xFF464747),
    onSecondary: Color(0xFFFFFFFF),
    secondaryContainer: Color(0xFFE3E2E2),
    onSecondaryContainer: Color(0xFF1A1C1C),

    tertiary: Color(0xFF353535),
    onTertiary: Color(0xFFFFFFFF),
    tertiaryContainer: Color(0xFFDADADA),
    onTertiaryContainer: Color(0xFF000000),

    error: Color(0xFFB3261E),
    onError: Color(0xFFFFFFFF),
    errorContainer: Color(0xFFF9DEDC),
    onErrorContainer: Color(0xFF410E0B),

    surface: Color(0xFFF7F7F7),
    onSurface: Color(0xFF1B1B1B),
    surfaceContainerLowest: Color(0xFFFFFFFF),
    surfaceContainerLow: Color(0xFFF2F2F2),
    surfaceContainer: Color(0xFFECECEC),
    surfaceContainerHigh: Color(0xFFE6E6E6),
    surfaceContainerHighest: Color(0xFFDFDFDF),

    onSurfaceVariant: Color(0xFF474747),
    outline: Color(0xFF767676),
    outlineVariant: Color(0xFFC6C6C6),

    shadow: Color(0xFF000000),
    scrim: Color(0xFF000000),

    inverseSurface: Color(0xFF2A2A2A),
    onInverseSurface: Color(0xFFF5F5F5),
    inversePrimary: Color(0xFFD4D4D4),

    surfaceTint: Color(0xFF5D5F5F),
  );
}
