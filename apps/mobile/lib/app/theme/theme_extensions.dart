import 'package:flutter/material.dart';
import 'app_radii.dart';

@immutable
class AppThemeTokens extends ThemeExtension<AppThemeTokens> {
  final BorderRadius radiusSm;
  final BorderRadius radiusMd;
  final BorderRadius radiusLg;
  final BorderRadius radiusXl;
  final double spaceXs;
  final double spaceSm;
  final double spaceMd;
  final double spaceLg;
  final double spaceXl;

  const AppThemeTokens({
    required this.radiusSm,
    required this.radiusMd,
    required this.radiusLg,
    required this.radiusXl,
    required this.spaceXs,
    required this.spaceSm,
    required this.spaceMd,
    required this.spaceLg,
    required this.spaceXl,
  });

  const AppThemeTokens.base()
      : radiusSm = AppRadii.radiusDefault,
        radiusMd = AppRadii.radiusLg,
        radiusLg = AppRadii.radiusXl,
        radiusXl = AppRadii.radiusFull,
        spaceXs = 4,
        spaceSm = 8,
        spaceMd = 12,
        spaceLg = 16,
        spaceXl = 24;

  @override
  AppThemeTokens copyWith({
    BorderRadius? radiusSm,
    BorderRadius? radiusMd,
    BorderRadius? radiusLg,
    BorderRadius? radiusXl,
    double? spaceXs,
    double? spaceSm,
    double? spaceMd,
    double? spaceLg,
    double? spaceXl,
  }) {
    return AppThemeTokens(
      radiusSm: radiusSm ?? this.radiusSm,
      radiusMd: radiusMd ?? this.radiusMd,
      radiusLg: radiusLg ?? this.radiusLg,
      radiusXl: radiusXl ?? this.radiusXl,
      spaceXs: spaceXs ?? this.spaceXs,
      spaceSm: spaceSm ?? this.spaceSm,
      spaceMd: spaceMd ?? this.spaceMd,
      spaceLg: spaceLg ?? this.spaceLg,
      spaceXl: spaceXl ?? this.spaceXl,
    );
  }

  @override
  AppThemeTokens lerp(ThemeExtension<AppThemeTokens>? other, double t) {
    if (other is! AppThemeTokens) return this;
    return AppThemeTokens(
      radiusSm: BorderRadius.lerp(radiusSm, other.radiusSm, t) ?? radiusSm,
      radiusMd: BorderRadius.lerp(radiusMd, other.radiusMd, t) ?? radiusMd,
      radiusLg: BorderRadius.lerp(radiusLg, other.radiusLg, t) ?? radiusLg,
      radiusXl: BorderRadius.lerp(radiusXl, other.radiusXl, t) ?? radiusXl,
      spaceXs: lerpDouble(spaceXs, other.spaceXs, t),
      spaceSm: lerpDouble(spaceSm, other.spaceSm, t),
      spaceMd: lerpDouble(spaceMd, other.spaceMd, t),
      spaceLg: lerpDouble(spaceLg, other.spaceLg, t),
      spaceXl: lerpDouble(spaceXl, other.spaceXl, t),
    );
  }

  static double lerpDouble(double a, double b, double t) => a + (b - a) * t;
}

extension ThemeDataX on ThemeData {
  AppThemeTokens get appTokens => extension<AppThemeTokens>()!;
}
