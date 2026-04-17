import 'package:flutter/material.dart';

abstract final class AppTextThemes {
  static TextTheme baseTextTheme(Color textColor) {
    return TextTheme(
      displayLarge: TextStyle(
        fontFamily: 'Manrope',
        fontSize: 40,
        fontWeight: FontWeight.w700,
        height: 1.1,
        color: textColor,
      ),
      displayMedium: TextStyle(
        fontFamily: 'Manrope',
        fontSize: 32,
        fontWeight: FontWeight.w700,
        height: 1.15,
        color: textColor,
      ),
      displaySmall: TextStyle(
        fontFamily: 'Manrope',
        fontSize: 28,
        fontWeight: FontWeight.w600,
        height: 1.2,
        color: textColor,
      ),
      headlineLarge: TextStyle(
        fontFamily: 'Manrope',
        fontSize: 24,
        fontWeight: FontWeight.w700,
        height: 1.2,
        color: textColor,
      ),
      headlineMedium: TextStyle(
        fontFamily: 'Manrope',
        fontSize: 22,
        fontWeight: FontWeight.w600,
        height: 1.25,
        color: textColor,
      ),
      headlineSmall: TextStyle(
        fontFamily: 'Manrope',
        fontSize: 20,
        fontWeight: FontWeight.w600,
        height: 1.25,
        color: textColor,
      ),
      titleLarge: TextStyle(
        fontFamily: 'Manrope',
        fontSize: 18,
        fontWeight: FontWeight.w600,
        height: 1.3,
        color: textColor,
      ),
      titleMedium: TextStyle(
        fontFamily: 'Inter',
        fontSize: 16,
        fontWeight: FontWeight.w600,
        height: 1.35,
        color: textColor,
      ),
      titleSmall: TextStyle(
        fontFamily: 'Inter',
        fontSize: 14,
        fontWeight: FontWeight.w600,
        height: 1.35,
        color: textColor,
      ),
      bodyLarge: TextStyle(
        fontFamily: 'Inter',
        fontSize: 16,
        fontWeight: FontWeight.w400,
        height: 1.45,
        color: textColor,
      ),
      bodyMedium: TextStyle(
        fontFamily: 'Inter',
        fontSize: 14,
        fontWeight: FontWeight.w400,
        height: 1.45,
        color: textColor,
      ),
      bodySmall: TextStyle(
        fontFamily: 'Inter',
        fontSize: 12,
        fontWeight: FontWeight.w400,
        height: 1.4,
        color: textColor,
      ),
      labelLarge: TextStyle(
        fontFamily: 'Inter',
        fontSize: 14,
        fontWeight: FontWeight.w600,
        height: 1.2,
        color: textColor,
      ),
      labelMedium: TextStyle(
        fontFamily: 'Inter',
        fontSize: 12,
        fontWeight: FontWeight.w600,
        height: 1.2,
        color: textColor,
      ),
      labelSmall: TextStyle(
        fontFamily: 'Inter',
        fontSize: 11,
        fontWeight: FontWeight.w500,
        height: 1.2,
        color: textColor,
      ),
    );
  }
}
