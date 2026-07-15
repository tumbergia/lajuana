import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/app_colors.dart';

/// Visual tokens for analytics charts and insight cards.
///
/// Domain / series accents are intentionally chromatic: the app
/// [ColorScheme] is near-monochrome, so charts need a dedicated palette
/// for category and series distinction. Status colors stay on [AppColors].
@immutable
class AnalyticsVisualTokens extends ThemeExtension<AnalyticsVisualTokens> {
  const AnalyticsVisualTokens({
    required this.domainAction,
    required this.domainReservations,
    required this.domainMoney,
    required this.domainExperiences,
    required this.domainParticipants,
    required this.domainEquines,
    required this.domainOperations,
    required this.success,
    required this.warning,
    required this.danger,
    required this.neutral,
    required this.seriesPalette,
    required this.gridColor,
    required this.tooltipBackground,
    required this.tooltipForeground,
    required this.chartHeightCompact,
    required this.chartHeightStandard,
    required this.chartHeightWide,
    required this.lineStrokeWidth,
    required this.barRadius,
    required this.dotSize,
    required this.animationDuration,
  });

  final Color domainAction;
  final Color domainReservations;
  final Color domainMoney;
  final Color domainExperiences;
  final Color domainParticipants;
  final Color domainEquines;
  final Color domainOperations;
  final Color success;
  final Color warning;
  final Color danger;
  final Color neutral;
  final List<Color> seriesPalette;
  final Color gridColor;
  final Color tooltipBackground;
  final Color tooltipForeground;
  final double chartHeightCompact;
  final double chartHeightStandard;
  final double chartHeightWide;
  final double lineStrokeWidth;
  final double barRadius;
  final double dotSize;
  final Duration animationDuration;

  /// Shared chromatic accents (readable on light and dark surfaces).
  static const Color _action = Color(0xFFFF9800);
  static const Color _reservations = Color(0xFF1E88E5);
  static const Color _money = Color(0xFF43A047);
  static const Color _experiences = Color(0xFF00897B);
  static const Color _participants = Color(0xFF5C6BC0);
  static const Color _equines = Color(0xFF8D6E63);
  static const Color _operations = Color(0xFF546E7A);
  static const Color _seriesCoral = Color(0xFFFF7043);
  static const Color _seriesAmber = Color(0xFFF9A825);

  factory AnalyticsVisualTokens.light(ColorScheme scheme) {
    return AnalyticsVisualTokens(
      domainAction: _action,
      domainReservations: _reservations,
      domainMoney: _money,
      domainExperiences: _experiences,
      domainParticipants: _participants,
      domainEquines: _equines,
      domainOperations: _operations,
      success: AppColors.success,
      warning: AppColors.warning,
      danger: AppColors.danger,
      neutral: scheme.onSurfaceVariant,
      seriesPalette: const [
        _reservations,
        _experiences,
        _money,
        _seriesAmber,
        _seriesCoral,
        _participants,
      ],
      gridColor: scheme.outlineVariant,
      tooltipBackground: scheme.inverseSurface,
      tooltipForeground: scheme.onInverseSurface,
      chartHeightCompact: 72,
      chartHeightStandard: 180,
      chartHeightWide: 240,
      lineStrokeWidth: 2.5,
      barRadius: 4,
      dotSize: 3.5,
      animationDuration: const Duration(milliseconds: 280),
    );
  }

  factory AnalyticsVisualTokens.dark(ColorScheme scheme) {
    return AnalyticsVisualTokens(
      domainAction: const Color(0xFFFFB74D),
      domainReservations: const Color(0xFF64B5F6),
      domainMoney: const Color(0xFF66BB6A),
      domainExperiences: const Color(0xFF4DB6AC),
      domainParticipants: const Color(0xFF7986CB),
      domainEquines: const Color(0xFFA1887F),
      domainOperations: const Color(0xFF90A4AE),
      success: AppColors.success,
      warning: AppColors.warning,
      danger: AppColors.danger,
      neutral: scheme.onSurfaceVariant,
      seriesPalette: const [
        Color(0xFF64B5F6),
        Color(0xFF4DB6AC),
        Color(0xFF66BB6A),
        Color(0xFFFFB74D),
        Color(0xFFFF8A65),
        Color(0xFF7986CB),
      ],
      gridColor: scheme.outlineVariant,
      tooltipBackground: scheme.inverseSurface,
      tooltipForeground: scheme.onInverseSurface,
      chartHeightCompact: 72,
      chartHeightStandard: 180,
      chartHeightWide: 240,
      lineStrokeWidth: 2.5,
      barRadius: 4,
      dotSize: 3.5,
      animationDuration: const Duration(milliseconds: 280),
    );
  }

  Color domainColor(String category) {
    switch (category) {
      case 'action':
        return domainAction;
      case 'reservations':
        return domainReservations;
      case 'money':
        return domainMoney;
      case 'experiences':
        return domainExperiences;
      case 'participants':
        return domainParticipants;
      case 'equines':
        return domainEquines;
      case 'operations':
        return domainOperations;
      default:
        return neutral;
    }
  }

  @override
  AnalyticsVisualTokens copyWith({
    Color? domainAction,
    Color? domainReservations,
    Color? domainMoney,
    Color? domainExperiences,
    Color? domainParticipants,
    Color? domainEquines,
    Color? domainOperations,
    Color? success,
    Color? warning,
    Color? danger,
    Color? neutral,
    List<Color>? seriesPalette,
    Color? gridColor,
    Color? tooltipBackground,
    Color? tooltipForeground,
    double? chartHeightCompact,
    double? chartHeightStandard,
    double? chartHeightWide,
    double? lineStrokeWidth,
    double? barRadius,
    double? dotSize,
    Duration? animationDuration,
  }) {
    return AnalyticsVisualTokens(
      domainAction: domainAction ?? this.domainAction,
      domainReservations: domainReservations ?? this.domainReservations,
      domainMoney: domainMoney ?? this.domainMoney,
      domainExperiences: domainExperiences ?? this.domainExperiences,
      domainParticipants: domainParticipants ?? this.domainParticipants,
      domainEquines: domainEquines ?? this.domainEquines,
      domainOperations: domainOperations ?? this.domainOperations,
      success: success ?? this.success,
      warning: warning ?? this.warning,
      danger: danger ?? this.danger,
      neutral: neutral ?? this.neutral,
      seriesPalette: seriesPalette ?? this.seriesPalette,
      gridColor: gridColor ?? this.gridColor,
      tooltipBackground: tooltipBackground ?? this.tooltipBackground,
      tooltipForeground: tooltipForeground ?? this.tooltipForeground,
      chartHeightCompact: chartHeightCompact ?? this.chartHeightCompact,
      chartHeightStandard: chartHeightStandard ?? this.chartHeightStandard,
      chartHeightWide: chartHeightWide ?? this.chartHeightWide,
      lineStrokeWidth: lineStrokeWidth ?? this.lineStrokeWidth,
      barRadius: barRadius ?? this.barRadius,
      dotSize: dotSize ?? this.dotSize,
      animationDuration: animationDuration ?? this.animationDuration,
    );
  }

  @override
  AnalyticsVisualTokens lerp(
    ThemeExtension<AnalyticsVisualTokens>? other,
    double t,
  ) {
    if (other is! AnalyticsVisualTokens) return this;
    Color c(Color a, Color b) => Color.lerp(a, b, t) ?? a;
    double d(double a, double b) => a + (b - a) * t;
    return AnalyticsVisualTokens(
      domainAction: c(domainAction, other.domainAction),
      domainReservations: c(domainReservations, other.domainReservations),
      domainMoney: c(domainMoney, other.domainMoney),
      domainExperiences: c(domainExperiences, other.domainExperiences),
      domainParticipants: c(domainParticipants, other.domainParticipants),
      domainEquines: c(domainEquines, other.domainEquines),
      domainOperations: c(domainOperations, other.domainOperations),
      success: c(success, other.success),
      warning: c(warning, other.warning),
      danger: c(danger, other.danger),
      neutral: c(neutral, other.neutral),
      seriesPalette: [
        for (var i = 0; i < seriesPalette.length; i++)
          c(
            seriesPalette[i],
            other.seriesPalette[i % other.seriesPalette.length],
          ),
      ],
      gridColor: c(gridColor, other.gridColor),
      tooltipBackground: c(tooltipBackground, other.tooltipBackground),
      tooltipForeground: c(tooltipForeground, other.tooltipForeground),
      chartHeightCompact: d(chartHeightCompact, other.chartHeightCompact),
      chartHeightStandard: d(chartHeightStandard, other.chartHeightStandard),
      chartHeightWide: d(chartHeightWide, other.chartHeightWide),
      lineStrokeWidth: d(lineStrokeWidth, other.lineStrokeWidth),
      barRadius: d(barRadius, other.barRadius),
      dotSize: d(dotSize, other.dotSize),
      animationDuration: t < 0.5 ? animationDuration : other.animationDuration,
    );
  }
}

extension AnalyticsThemeDataX on ThemeData {
  AnalyticsVisualTokens get analyticsTokens =>
      extension<AnalyticsVisualTokens>() ??
      AnalyticsVisualTokens.light(colorScheme);
}
