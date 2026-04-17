import 'package:flutter/material.dart';
import 'app_radii.dart';

@immutable
class AppThemeTokens extends ThemeExtension<AppThemeTokens> {
  final BorderRadius radiusSm;
  final BorderRadius radiusMd;
  final BorderRadius radiusLg;
  final BorderRadius radiusXl;

  const AppThemeTokens({
    required this.radiusSm,
    required this.radiusMd,
    required this.radiusLg,
    required this.radiusXl,
  });

  const AppThemeTokens.base()
      : radiusSm = AppRadii.radiusDefault,
        radiusMd = AppRadii.radiusLg,
        radiusLg = AppRadii.radiusXl,
        radiusXl = AppRadii.radiusFull;

  @override
  AppThemeTokens copyWith({
    BorderRadius? radiusSm,
    BorderRadius? radiusMd,
    BorderRadius? radiusLg,
    BorderRadius? radiusXl,
  }) {
    return AppThemeTokens(
      radiusSm: radiusSm ?? this.radiusSm,
      radiusMd: radiusMd ?? this.radiusMd,
      radiusLg: radiusLg ?? this.radiusLg,
      radiusXl: radiusXl ?? this.radiusXl,
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
    );
  }
}

extension ThemeDataX on ThemeData {
  AppThemeTokens get appTokens => extension<AppThemeTokens>()!;
}
