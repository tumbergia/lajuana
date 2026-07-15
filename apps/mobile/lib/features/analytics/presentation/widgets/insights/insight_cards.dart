import 'package:country_flags/country_flags.dart';
import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_loading_skeleton.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_donut_chart.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_line_chart.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_sparkline.dart';
import 'package:mobile/features/analytics/presentation/widgets/country_flag_colors.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_card_shell.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/indicator_detail_sheet.dart';
import 'package:mobile/features/providers/presentation/utils/phone_country.dart';

List<AppChartPoint> chartPointsFromSeries(AnalyticsSeries series) {
  return [
    for (final p in series.points)
      AppChartPoint(label: p.label, value: p.raw),
  ];
}

List<AppChartPoint> chartPointsFromRanking(List<RankingItem> ranking) {
  return [
    for (final r in ranking.take(5))
      AppChartPoint(label: r.label, value: r.rawValue),
  ];
}

List<AppChartPoint> chartPointsFromBreakdown(List<BreakdownItem> items) {
  return [
    for (final b in items) AppChartPoint(label: b.label, value: b.rawValue),
  ];
}

/// Status / series color for a donut-style breakdown row.
Color breakdownItemColor(
  BuildContext context,
  AnalyticsModule module,
  BreakdownItem item,
  int index,
) {
  final tokens = Theme.of(context).analyticsTokens;
  const statusWhite = Colors.white;
  const statusGreen = Color(0xFF81C784);
  if (module.id == 'reservation_status') {
    switch (item.key) {
      case 'payment_received':
        return statusWhite;
      case 'confirmed':
      case 'completed':
        return statusGreen;
      case 'pending_payment':
        return tokens.warning;
      case 'cancelled':
      case 'expired':
        return tokens.danger;
    }
  }
  if (module.id == 'payment_status') {
    switch (item.key) {
      case 'pending':
        return tokens.warning;
      case 'received':
        return statusWhite;
      case 'verified':
        return statusGreen;
      case 'rejected':
        return tokens.danger;
    }
  }
  if (module.id == 'participant_readiness') {
    switch (item.key) {
      case 'completed':
        return tokens.success;
      case 'pending':
        return tokens.warning;
    }
  }
  if (module.id == 'reservation_origins') {
    switch (item.key) {
      case 'whatsapp':
        return const Color(0xFF25D366);
      case 'facebook':
        return const Color(0xFF1877F2);
      case 'instagram':
        return const Color(0xFFE1306C);
      case 'email':
        return const Color(0xFF64748B);
    }
  }
  return tokens.seriesPalette[index % tokens.seriesPalette.length];
}

Color _occupancyRowColor(AnalyticsVisualTokens tokens, RankingItem item) {
  final share = item.sharePercentage;
  if (share == null) return tokens.neutral;
  if (share < 25) return tokens.danger;
  if (share < 75) return tokens.warning;
  return tokens.success;
}

/// Vivid series for experience rankings (readable on dark cards).
const List<Color> _experiencesVividPalette = [
  Color(0xFF00E676), // neon green
  Color(0xFFFF9100), // vivid orange
  Color(0xFF40C4FF), // bright sky
  Color(0xFFE040FB), // vivid magenta
  Color(0xFFFFEA00), // electric yellow
  Color(0xFF7C4DFF), // vivid violet
];

Color _rankingBarColor(AnalyticsModule module, AnalyticsVisualTokens tokens, int index) {
  if (module.id == 'top_experiences') {
    return _experiencesVividPalette[index % _experiencesVividPalette.length];
  }
  return tokens.seriesPalette[index % tokens.seriesPalette.length];
}

/// Card chrome (lateral strip + insight callout) follows the visual top-1.
Color chromeAccentForModule(BuildContext context, AnalyticsModule module) {
  final tokens = Theme.of(context).analyticsTokens;
  final scheme = Theme.of(context).colorScheme;
  final fallback = tokens.domainColor(module.category);

  if (module.ranking.isNotEmpty) {
    final top = module.ranking.first;
    if (module.id == 'top_countries') {
      return countryFlagColor(
        _Flag._resolveIso(top.countryCode, top.countryName ?? top.label),
        fallback: scheme.outline,
      );
    }
    if (module.id == 'occupancy') {
      return _occupancyRowColor(tokens, top);
    }
    if (module.id == 'top_experiences') {
      return _experiencesVividPalette.first;
    }
    return tokens.seriesPalette[0];
  }

  if (module.breakdown.isNotEmpty) {
    var topIndex = 0;
    for (var i = 1; i < module.breakdown.length; i++) {
      if (module.breakdown[i].rawValue > module.breakdown[topIndex].rawValue) {
        topIndex = i;
      }
    }
    return breakdownItemColor(
      context,
      module,
      module.breakdown[topIndex],
      topIndex,
    );
  }

  // Trends / KPI: the painted series uses the domain accent as its only color.
  return fallback;
}

Widget _emptyCard(AnalyticsModule module, {required bool refreshing}) {
  return Builder(
    builder: (context) {
      return InsightCardShell(
        title: module.title,
        periodLabel: module.period.dateRangeLabel,
        insightText: module.emptyMessage ?? module.insightText,
        refreshing: refreshing,
        accentColor: chromeAccentForModule(context, module),
        child: AppChartEmptyState(
          title: 'Sin datos',
          message: module.emptyMessage ?? 'Todavía no hay datos para este periodo.',
        ),
      );
    },
  );
}

/// Minimal tinted surface (no shared header/value skeleton).
class _VizSurface extends StatelessWidget {
  const _VizSurface({
    required this.accent,
    required this.child,
  });

  final Color accent;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    return AppCard(
      accentColor: accent,
      padding: EdgeInsets.all(tokens.spaceLg),
      child: child,
    );
  }
}

class KpiInsightCard extends StatelessWidget {
  const KpiInsightCard({
    super.key,
    required this.module,
    this.onAction,
    this.refreshing = false,
  });

  final AnalyticsModule module;
  final VoidCallback? onAction;
  final bool refreshing;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    if (module.isEmpty) {
      return _emptyCard(module, refreshing: refreshing);
    }
    final sparkValues = module.breakdown.isNotEmpty
        ? module.breakdown.map((b) => b.rawValue).toList()
        : <double>[module.primaryValue?.raw ?? 0];
    final accent = chromeAccentForModule(context, module);
    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TitleRow(
            title: module.title,
            period: module.period.label,
            refreshing: refreshing,
            onInfo: () => showIndicatorDetailSheet(context, module: module),
          ),
          SizedBox(height: Theme.of(context).appTokens.spaceMd),
          if (module.primaryValue != null)
            Text(
              module.primaryValue!.formatted,
              style: Theme.of(context).textTheme.displaySmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: accent,
                  ),
            ),
          if (module.primaryValue != null)
            Text(
              module.primaryValue!.unit,
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          SizedBox(height: Theme.of(context).appTokens.spaceSm),
          AppSparkline(
            values: sparkValues,
            semanticSummary: module.insightText ?? module.title,
            color: accent,
            height: tokens.chartHeightCompact,
          ),
          if (module.insightText != null) ...[
            SizedBox(height: Theme.of(context).appTokens.spaceMd),
            Text(module.insightText!),
          ],
        ],
      ),
    );
  }
}

/// Contexto primero: qué mide, qué tan fuerte cambió y cómo se movió en el
/// tiempo. El número + flecha de tendencia son lo primero que se lee.
class TrendInsightCard extends StatelessWidget {
  const TrendInsightCard({
    super.key,
    required this.module,
    this.compact = false,
    this.onAction,
    this.refreshing = false,
    this.hero = false,
  });

  final AnalyticsModule module;
  final bool compact;
  final VoidCallback? onAction;
  final bool refreshing;
  final bool hero;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final appTokens = Theme.of(context).appTokens;
    final scheme = Theme.of(context).colorScheme;
    if (module.isEmpty || module.series.isEmpty) {
      return _emptyCard(module, refreshing: refreshing);
    }
    final series = module.series.first;
    final points = chartPointsFromSeries(series);
    final accent = chromeAccentForModule(context, module);
    final chartHeight = hero
        ? tokens.chartHeightWide + 24
        : compact
            ? tokens.chartHeightStandard
            : tokens.chartHeightWide;
    final description = module.description.trim();
    final seriesLabel = series.label.trim();
    final showSeriesCaption =
        seriesLabel.isNotEmpty && seriesLabel.toLowerCase() != module.title.toLowerCase();

    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  module.title,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
              if (refreshing) const ChartRefreshingBadge(),
              IconButton(
                visualDensity: VisualDensity.compact,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                tooltip: 'Detalle y descarga',
                onPressed: () =>
                    showIndicatorDetailSheet(context, module: module),
                icon: Icon(
                  Icons.info_outline_rounded,
                  size: 18,
                  color: scheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
          if (description.isNotEmpty) ...[
            SizedBox(height: appTokens.spaceXs),
            Text(
              description,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ],
          SizedBox(height: appTokens.spaceXs),
          Text(
            module.period.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          SizedBox(height: appTokens.spaceLg),
          if (module.primaryValue != null)
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  module.primaryValue!.formatted,
                  style: (hero
                          ? Theme.of(context).textTheme.headlineLarge
                          : Theme.of(context).textTheme.headlineMedium)
                      ?.copyWith(
                    fontWeight: FontWeight.w900,
                    color: accent,
                  ),
                ),
                SizedBox(width: appTokens.spaceSm),
                Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Text(
                    module.primaryValue!.unit,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                  ),
                ),
                const Spacer(),
                if (module.comparison != null)
                  _TrendDeltaChip(comparison: module.comparison!, tokens: tokens),
              ],
            ),
          if (module.comparison?.label != null) ...[
            SizedBox(height: appTokens.spaceXs),
            Text(
              module.comparison!.label!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ],
          SizedBox(height: appTokens.spaceLg),
          if (showSeriesCaption) ...[
            Text(
              seriesLabel.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.6,
                  ),
            ),
            SizedBox(height: appTokens.spaceSm),
          ],
          SizedBox(
            // Allow the lowered X-label band (~40px) without crushing the plot.
            height: chartHeight + AppLineChart.xAxisLabelBandExtra,
            width: double.infinity,
            child: RepaintBoundary(
              child: AppLineChart(
                series: AppChartSeries(
                  label: series.label,
                  points: points,
                  color: accent,
                ),
                semanticSummary: module.insightText ?? module.title,
                unit: series.unit,
                height: chartHeight,
                hero: true,
                periodStart: DateTime.tryParse(module.period.start),
                periodEnd: DateTime.tryParse(module.period.end),
                periodPreset: module.period.preset,
              ),
            ),
          ),
          if (module.insightText != null) ...[
            SizedBox(height: appTokens.spaceLg),
            _InsightCallout(text: module.insightText!, accent: accent),
          ],
        ],
      ),
    );
  }
}

/// Direction-aware pill: color + arrow make the trend readable without text.
class _TrendDeltaChip extends StatelessWidget {
  const _TrendDeltaChip({required this.comparison, required this.tokens});

  final AnalyticsComparison comparison;
  final AnalyticsVisualTokens tokens;

  @override
  Widget build(BuildContext context) {
    final delta = comparison.percentageDelta;
    final absFormatted = comparison.absoluteFormatted?.trim();
    Color color;
    IconData icon;
    String text;
    if (delta != null && delta.abs() >= 0.5) {
      final positive = delta > 0;
      color = positive ? tokens.success : tokens.danger;
      icon = positive ? Icons.trending_up_rounded : Icons.trending_down_rounded;
      text = '${positive ? '+' : ''}${delta.toStringAsFixed(0)}%';
    } else if (delta != null) {
      color = tokens.neutral;
      icon = Icons.trending_flat_rounded;
      text = 'Estable';
    } else if (absFormatted != null && absFormatted.isNotEmpty) {
      final positive = absFormatted.startsWith('+');
      final negative = absFormatted.startsWith('-');
      color = positive ? tokens.success : (negative ? tokens.danger : tokens.neutral);
      icon = positive
          ? Icons.trending_up_rounded
          : (negative ? Icons.trending_down_rounded : Icons.trending_flat_rounded);
      text = absFormatted;
    } else {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 4),
          Text(
            text,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w800,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

/// Narrative summary set apart from the raw numbers so it reads as "what
/// this means" rather than more data.
class _InsightCallout extends StatelessWidget {
  const _InsightCallout({required this.text, required this.accent});

  final String text;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final appTokens = Theme.of(context).appTokens;
    return Container(
      padding: EdgeInsets.all(appTokens.spaceMd),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.10),
        borderRadius: appTokens.radiusMd,
        border: Border.all(color: accent.withValues(alpha: 0.24)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.lightbulb_outline_rounded, size: 18, color: accent),
          SizedBox(width: appTokens.spaceSm),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Ranking horizontal con acento de dominio, share % e insight callout.
class RankingInsightCard extends StatelessWidget {
  const RankingInsightCard({
    super.key,
    required this.module,
    this.onAction,
    this.refreshing = false,
    this.compact = false,
    this.hero = false,
  });

  final AnalyticsModule module;
  final VoidCallback? onAction;
  final bool refreshing;
  final bool compact;
  final bool hero;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final appTokens = Theme.of(context).appTokens;
    final scheme = Theme.of(context).colorScheme;
    if (module.isEmpty || module.ranking.isEmpty) {
      return _emptyCard(module, refreshing: refreshing);
    }
    final items = module.ranking.take(hero ? 6 : 5).toList();
    final maxV =
        items.map((e) => e.rawValue).fold<double>(1, (a, b) => a > b ? a : b);
    final description = module.description.trim();
    final accent = chromeAccentForModule(context, module);

    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  module.title,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
              if (refreshing) const ChartRefreshingBadge(),
              IconButton(
                visualDensity: VisualDensity.compact,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                tooltip: 'Detalle y descarga',
                onPressed: () =>
                    showIndicatorDetailSheet(context, module: module),
                icon: Icon(
                  Icons.info_outline_rounded,
                  size: 18,
                  color: scheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
          if (description.isNotEmpty) ...[
            SizedBox(height: appTokens.spaceXs),
            Text(
              description,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ],
          SizedBox(height: appTokens.spaceXs),
          Text(
            module.period.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          if (module.primaryValue != null) ...[
            SizedBox(height: appTokens.spaceLg),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  module.primaryValue!.formatted,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                        color: accent,
                      ),
                ),
                SizedBox(width: appTokens.spaceSm),
                Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Text(
                    module.primaryValue!.unit,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                  ),
                ),
              ],
            ),
          ],
          SizedBox(height: appTokens.spaceLg),
          for (var i = 0; i < items.length; i++) ...[
            if (i > 0) SizedBox(height: appTokens.spaceMd),
            _MetricBarRow(
              label: items[i].label,
              valueText: items[i].formattedValue,
              sharePercentage: items[i].sharePercentage,
              fraction: (items[i].rawValue / maxV).clamp(0.0, 1.0),
              barColor: _rankingBarColor(module, tokens, i),
              barHeight: hero ? 14 : 11,
            ),
          ],
          if (module.insightText != null) ...[
            SizedBox(height: appTokens.spaceLg),
            _InsightCallout(text: module.insightText!, accent: accent),
          ],
        ],
      ),
    );
  }
}

/// Progress rows: occupancy usa % real + colores de umbral; el resto escala
/// por valor relativo con la paleta de series.
class ProgressInsightCard extends StatelessWidget {
  const ProgressInsightCard({
    super.key,
    required this.module,
    this.onAction,
    this.refreshing = false,
    this.hero = false,
  });

  final AnalyticsModule module;
  final VoidCallback? onAction;
  final bool refreshing;
  final bool hero;

  bool get _isOccupancy => module.id == 'occupancy';

  /// Prefer API `X/max`; normalize legacy `"N participantes"` to `N/—`.
  static String _occupancyValueText(RankingItem item) {
    final raw = item.formattedValue.trim();
    if (raw.contains('/')) return raw;
    final digits = RegExp(r'^(\d+)').firstMatch(raw)?.group(1);
    if (digits != null) return '$digits/—';
    if (item.rawValue == item.rawValue.roundToDouble()) {
      return '${item.rawValue.toInt()}/—';
    }
    return raw.isNotEmpty ? raw : '${item.rawValue.toStringAsFixed(0)}/—';
  }

  Color _barColor(
    AnalyticsVisualTokens tokens,
    RankingItem item,
    int index,
  ) {
    if (_isOccupancy) return _occupancyRowColor(tokens, item);
    return tokens.seriesPalette[index % tokens.seriesPalette.length];
  }

  double _fraction(RankingItem item, double maxRaw) {
    if (_isOccupancy && item.sharePercentage != null) {
      return (item.sharePercentage! / 100).clamp(0.0, 1.0);
    }
    return (item.rawValue / maxRaw).clamp(0.0, 1.0);
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final appTokens = Theme.of(context).appTokens;
    final scheme = Theme.of(context).colorScheme;
    final items = module.ranking.isNotEmpty
        ? module.ranking
        : [
            for (var i = 0; i < module.breakdown.length; i++)
              RankingItem(
                rank: module.breakdown[i].rank ?? i + 1,
                key: module.breakdown[i].key,
                label: module.breakdown[i].label,
                rawValue: module.breakdown[i].rawValue,
                formattedValue: module.breakdown[i].formattedValue,
                unit: module.breakdown[i].unit,
                sharePercentage: module.breakdown[i].sharePercentage,
              ),
          ];
    if (module.isEmpty || items.isEmpty) {
      return _emptyCard(module, refreshing: refreshing);
    }
    final maxV =
        items.map((e) => e.rawValue).fold<double>(1, (a, b) => a > b ? a : b);
    final shown = items.take(hero ? 6 : 5).toList();
    final description = module.description.trim();
    final accent = chromeAccentForModule(context, module);

    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  module.title,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
              if (refreshing) const ChartRefreshingBadge(),
              IconButton(
                visualDensity: VisualDensity.compact,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                tooltip: 'Detalle y descarga',
                onPressed: () =>
                    showIndicatorDetailSheet(context, module: module),
                icon: Icon(
                  Icons.info_outline_rounded,
                  size: 18,
                  color: scheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
          if (description.isNotEmpty) ...[
            SizedBox(height: appTokens.spaceXs),
            Text(
              description,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ],
          SizedBox(height: appTokens.spaceXs),
          Text(
            module.period.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          if (module.primaryValue != null) ...[
            SizedBox(height: appTokens.spaceLg),
            Builder(
              builder: (context) {
                var primaryFormatted = module.primaryValue!.formatted;
                var primaryUnit = module.primaryValue!.unit;
                if (_isOccupancy) {
                  if (!primaryFormatted.contains('/') && shown.isNotEmpty) {
                    primaryFormatted = _occupancyValueText(shown.first);
                  } else if (!primaryFormatted.contains('/')) {
                    primaryFormatted = _occupancyValueText(
                      RankingItem(
                        rank: 1,
                        key: 'occupancy-primary',
                        label: '',
                        rawValue: module.primaryValue!.raw,
                        formattedValue: primaryFormatted,
                        unit: primaryUnit,
                      ),
                    );
                  }
                  primaryUnit = '';
                }
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      primaryFormatted,
                      style:
                          Theme.of(context).textTheme.headlineMedium?.copyWith(
                                fontWeight: FontWeight.w900,
                                color: accent,
                              ),
                    ),
                    if (primaryUnit.isNotEmpty) ...[
                      SizedBox(width: appTokens.spaceSm),
                      Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Text(
                          primaryUnit,
                          style:
                              Theme.of(context).textTheme.labelLarge?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                  ),
                        ),
                      ),
                    ],
                  ],
                );
              },
            ),
          ],
          SizedBox(height: appTokens.spaceLg),
          for (var i = 0; i < shown.length; i++) ...[
            if (i > 0) SizedBox(height: appTokens.spaceMd),
            _MetricBarRow(
              label: shown[i].label,
              valueText: _isOccupancy
                  ? _occupancyValueText(shown[i])
                  : shown[i].formattedValue,
              sharePercentage: shown[i].sharePercentage,
              fraction: _fraction(shown[i], maxV),
              barColor: _barColor(tokens, shown[i], i),
              barHeight: hero ? 14 : 11,
              emphasizeShare: _isOccupancy,
            ),
          ],
          if (module.insightText != null) ...[
            SizedBox(height: appTokens.spaceLg),
            _InsightCallout(text: module.insightText!, accent: accent),
          ],
        ],
      ),
    );
  }
}

/// Shared ranking/progress row: label + value + optional share + bar.
/// Same layout for every row (including top 1) so no info is dropped.
class _MetricBarRow extends StatelessWidget {
  const _MetricBarRow({
    required this.label,
    required this.valueText,
    required this.fraction,
    required this.barColor,
    required this.barHeight,
    this.sharePercentage,
    this.emphasizeShare = false,
  });

  final String label;
  final String valueText;
  final double? sharePercentage;
  final double fraction;
  final Color barColor;
  final double barHeight;
  final bool emphasizeShare;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final appTokens = Theme.of(context).appTokens;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                label,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ),
            SizedBox(width: appTokens.spaceSm),
            Text(
              valueText,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            if (emphasizeShare) ...[
              SizedBox(width: appTokens.spaceXs),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: barColor.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  sharePercentage != null
                      ? '${sharePercentage!.toStringAsFixed(0)}%'
                      : '—',
                  style: TextStyle(
                    color: barColor,
                    fontWeight: FontWeight.w800,
                    fontSize: 11,
                  ),
                ),
              ),
            ] else if (sharePercentage != null) ...[
              SizedBox(width: appTokens.spaceXs),
              Text(
                '${sharePercentage!.toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ],
          ],
        ),
        SizedBox(height: appTokens.spaceXs + 2),
        _TintedBar(
          fraction: fraction,
          color: barColor,
          height: barHeight,
        ),
      ],
    );
  }
}

class _TintedBar extends StatelessWidget {
  const _TintedBar({
    required this.fraction,
    required this.color,
    required this.height,
  });

  final double fraction;
  final Color color;
  final double height;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final radius = BorderRadius.circular(
      Theme.of(context).analyticsTokens.barRadius + 2,
    );
    return ClipRRect(
      borderRadius: radius,
      child: SizedBox(
        height: height,
        width: double.infinity,
        child: Stack(
          fit: StackFit.expand,
          children: [
            ColoredBox(color: scheme.surfaceContainerHighest),
            FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: fraction.clamp(0.0, 1.0),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      color.withValues(alpha: 0.82),
                      color,
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class CountryRankingCard extends StatelessWidget {
  const CountryRankingCard({
    super.key,
    required this.module,
    this.onAction,
    this.refreshing = false,
    this.hero = false,
  });

  final AnalyticsModule module;
  final VoidCallback? onAction;
  final bool refreshing;
  final bool hero;

  static const int _visibleLimit = 5;

  void _openInfo(BuildContext context, {RankingItem? focus}) {
    showIndicatorDetailSheet(context, module: module);
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final scheme = Theme.of(context).colorScheme;
    final appTokens = Theme.of(context).appTokens;
    if (module.isEmpty || module.ranking.isEmpty) {
      return InsightCardShell(
        title: module.title,
        periodLabel: module.period.dateRangeLabel,
        insightText: module.emptyMessage ?? module.insightText,
        refreshing: refreshing,
        accentColor: chromeAccentForModule(context, module),
        child: AppChartEmptyState(
          message: module.emptyMessage ??
              'Aún no hay suficientes participantes registrados para mostrar países principales.',
          icon: Icons.public,
        ),
      );
    }

    final allItems = module.ranking;
    final items = allItems.take(_visibleLimit).toList();
    final hasMore = allItems.length > _visibleLimit;
    final total = items.fold<double>(0, (sum, item) => sum + item.rawValue);
    final points = [
      for (final item in items)
        AppChartPoint(
          label: item.countryName ?? item.label,
          value: item.rawValue,
          color: countryFlagColor(
            _Flag._resolveIso(item.countryCode, item.countryName ?? item.label),
            fallback: scheme.outline,
          ),
        ),
    ];
    final accent = chromeAccentForModule(context, module);

    return AppCard(
      accentColor: accent,
      padding: EdgeInsets.all(appTokens.spaceLg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => _openInfo(context),
              borderRadius: appTokens.radiusMd,
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: appTokens.spaceXs),
                child: Row(
                  children: [
                    Icon(Icons.public, color: accent, size: 22),
                    SizedBox(width: appTokens.spaceSm),
                    Expanded(
                      child: Text(
                        module.title,
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                      ),
                    ),
                    if (refreshing) const ChartRefreshingBadge(),
                    Icon(
                      Icons.info_outline_rounded,
                      size: 18,
                      color: scheme.onSurfaceVariant,
                    ),
                  ],
                ),
              ),
            ),
          ),
          Text(
            module.period.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          SizedBox(height: appTokens.spaceMd),
          AppDonutChart(
            points: points,
            semanticSummary: module.insightText ?? module.title,
            centerLabel: total == total.roundToDouble()
                ? '${total.toInt()}'
                : total.toStringAsFixed(0),
            height: hero ? tokens.chartHeightWide : tokens.chartHeightStandard,
            showLegend: false,
            onSectionTap: (index) {
              if (index < 0 || index >= items.length) {
                _openInfo(context);
                return;
              }
              _openInfo(context, focus: items[index]);
            },
          ),
          SizedBox(height: appTokens.spaceMd),
          for (var i = 0; i < items.length; i++) ...[
            if (i > 0) SizedBox(height: appTokens.spaceSm),
            _CountryLegendRow(
              item: items[i],
              color: points[i].color ?? scheme.outline,
              onTap: () => _openInfo(context, focus: items[i]),
            ),
          ],
          if (hasMore) ...[
            SizedBox(height: appTokens.spaceMd),
            Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: () => _openInfo(context),
                borderRadius: appTokens.radiusMd,
                child: Padding(
                  padding: EdgeInsets.symmetric(vertical: appTokens.spaceXs),
                  child: Text(
                    'Mostrando top $_visibleLimit · toca para ver todos (${allItems.length})',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                  ),
                ),
              ),
            ),
          ],
          if (module.insightText != null) ...[
            SizedBox(height: appTokens.spaceMd),
            _InsightCallout(text: module.insightText!, accent: accent),
          ],
        ],
      ),
    );
  }
}

class _CountryLegendRow extends StatelessWidget {
  const _CountryLegendRow({
    required this.item,
    required this.color,
    this.onTap,
  });

  final RankingItem item;
  final Color color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final appTokens = Theme.of(context).appTokens;
    final share = item.sharePercentage;
    final row = Padding(
      padding: EdgeInsets.symmetric(
        horizontal: appTokens.spaceSm,
        vertical: appTokens.spaceXs,
      ),
      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          SizedBox(width: appTokens.spaceSm),
          _Flag(
            code: item.countryCode,
            name: item.countryName ?? item.label,
            width: 22,
            height: 16,
          ),
          SizedBox(width: appTokens.spaceSm),
          Expanded(
            child: Text(
              item.countryName ?? item.label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ),
          Text(
            item.formattedValue,
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          if (share != null) ...[
            SizedBox(width: appTokens.spaceXs),
            Text(
              '${share.toStringAsFixed(0)}%',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ],
        ],
      ),
    );

    if (onTap == null) return row;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: appTokens.radiusMd,
        child: row,
      ),
    );
  }
}

class _Flag extends StatelessWidget {
  const _Flag({
    this.code,
    this.name,
    this.width = 36,
    this.height = 26,
  });

  final String? code;
  final String? name;
  final double width;
  final double height;

  /// Resolves ISO via the same phone-country catalog used when muting AI
  /// numbers ([kPhoneCountries]), then renders with [CountryFlag].
  static String? _resolveIso(String? code, String? name) {
    final rawCode = code?.trim().toUpperCase();
    if (rawCode != null &&
        rawCode.length == 2 &&
        rawCode != 'OTHERS' &&
        rawCode != 'UNKNOWN') {
      final byCode = kPhoneCountries.where((c) => c.iso == rawCode);
      if (byCode.isNotEmpty) return byCode.first.iso;
      // Still a plausible ISO even if missing from the phone list.
      return rawCode;
    }
    final needle = name?.trim().toLowerCase();
    if (needle == null || needle.isEmpty) return null;
    for (final country in kPhoneCountries) {
      if (country.name.toLowerCase() == needle ||
          country.iso.toLowerCase() == needle) {
        return country.iso;
      }
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final iso = _resolveIso(code, name);
    if (iso == null) {
      return Icon(
        Icons.public,
        size: height + 4,
        color: scheme.onSurfaceVariant,
      );
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(3),
      child: CountryFlag.fromCountryCode(iso, width: width, height: height),
    );
  }
}

class ActionCenterCard extends StatelessWidget {
  const ActionCenterCard({
    super.key,
    required this.module,
    this.onItemTap,
    this.refreshing = false,
  });

  final AnalyticsModule module;
  final void Function(BreakdownItem item)? onItemTap;
  final bool refreshing;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    if (module.isEmpty || module.breakdown.isEmpty) {
      return InsightCardShell(
        title: module.title,
        periodLabel: module.period.dateRangeLabel,
        insightText: module.emptyMessage ?? 'No hay pendientes críticos.',
        accentColor: tokens.success,
        refreshing: refreshing,
        chartFirst: false,
        onInfo: () => showIndicatorDetailSheet(context, module: module),
        child: AppChartEmptyState(
          message: module.emptyMessage ?? 'No hay pendientes críticos.',
          icon: Icons.check_circle_outline,
        ),
      );
    }
    final scheme = Theme.of(context).colorScheme;
    final tokensApp = Theme.of(context).appTokens;
    final insight = module.insightText?.trim();
    return InsightCardShell(
      title: module.title,
      periodLabel: '',
      accentColor: tokens.warning,
      refreshing: refreshing,
      chartFirst: false,
      onInfo: () => showIndicatorDetailSheet(context, module: module),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (insight != null && insight.isNotEmpty) ...[
            Text(insight, style: Theme.of(context).textTheme.bodyMedium),
            SizedBox(height: tokensApp.spaceMd),
          ],
          for (final item in module.breakdown)
            Padding(
              padding: EdgeInsets.only(bottom: tokensApp.spaceSm),
              child: AppEntityRowCard(
                title: item.label,
                subtitle: '',
                wrapTitle: true,
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      item.formattedValue,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                            color: scheme.onSurface,
                          ),
                    ),
                    if (onItemTap != null) ...[
                      SizedBox(width: tokensApp.spaceXs),
                      Icon(
                        Icons.chevron_right_rounded,
                        size: 18,
                        color: scheme.onSurfaceVariant,
                      ),
                    ],
                  ],
                ),
                onTap: onItemTap == null ? null : () => onItemTap!(item),
              ),
            ),
        ],
      ),
    );
  }
}

/// Donut a la izquierda + leyenda a la derecha (layout distinto a tendencia).
///
/// Tap en sección / leyenda / botón info abre el desglose (mismo patrón que
/// [CountryRankingCard]).
class DonutInsightCard extends StatelessWidget {
  const DonutInsightCard({
    super.key,
    required this.module,
    this.onAction,
    this.refreshing = false,
    this.compact = false,
    this.hero = false,
  });

  final AnalyticsModule module;
  final VoidCallback? onAction;
  final bool refreshing;
  final bool compact;
  final bool hero;

  Color _colorForItem(BuildContext context, BreakdownItem item, int index) {
    return breakdownItemColor(context, module, item, index);
  }

  void _openInfo(BuildContext context, {BreakdownItem? focus}) {
    showIndicatorDetailSheet(context, module: module);
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final scheme = Theme.of(context).colorScheme;
    final appTokens = Theme.of(context).appTokens;
    final items = module.breakdown;
    if (module.isEmpty || items.isEmpty) {
      return _emptyCard(module, refreshing: refreshing);
    }
    final points = [
      for (var i = 0; i < items.length; i++)
        AppChartPoint(
          label: items[i].label,
          value: items[i].rawValue,
          color: _colorForItem(context, items[i], i),
        ),
    ];
    final accent = chromeAccentForModule(context, module);
    final h = hero
        ? tokens.chartHeightWide
        : compact
            ? tokens.chartHeightStandard * 0.85
            : tokens.chartHeightStandard;

    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => _openInfo(context),
              borderRadius: appTokens.radiusMd,
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: appTokens.spaceXs),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        module.title,
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                      ),
                    ),
                    if (refreshing) const ChartRefreshingBadge(),
                    Icon(
                      Icons.info_outline_rounded,
                      size: 18,
                      color: scheme.onSurfaceVariant,
                    ),
                  ],
                ),
              ),
            ),
          ),
          Text(
            module.period.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          SizedBox(height: appTokens.spaceMd),
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Expanded(
                flex: 5,
                child: RepaintBoundary(
                  child: AppDonutChart(
                    points: points,
                    semanticSummary: module.insightText ?? module.title,
                    centerLabel: module.primaryValue?.formatted,
                    height: h,
                    showLegend: false,
                    onSectionTap: (index) {
                      if (index < 0 || index >= items.length) {
                        _openInfo(context);
                        return;
                      }
                      _openInfo(context, focus: items[index]);
                    },
                  ),
                ),
              ),
              SizedBox(width: appTokens.spaceMd),
              Expanded(
                flex: 4,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (var i = 0; i < items.length; i++) ...[
                      if (i > 0) SizedBox(height: appTokens.spaceSm),
                      _BreakdownLegendRow(
                        item: items[i],
                        color: points[i].color ??
                            tokens.seriesPalette[
                                i % tokens.seriesPalette.length],
                        onTap: () => _openInfo(context, focus: items[i]),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          if (module.insightText != null) ...[
            SizedBox(height: appTokens.spaceMd),
            _InsightCallout(text: module.insightText!, accent: accent),
          ],
        ],
      ),
    );
  }
}

class _BreakdownLegendRow extends StatelessWidget {
  const _BreakdownLegendRow({
    required this.item,
    required this.color,
    this.onTap,
  });

  final BreakdownItem item;
  final Color color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final appTokens = Theme.of(context).appTokens;
    final share = item.sharePercentage;
    final valueText = item.formattedValue.isNotEmpty
        ? item.formattedValue
        : (item.rawValue == item.rawValue.roundToDouble()
            ? item.rawValue.toInt().toString()
            : item.rawValue.toStringAsFixed(1));
    final isLight = color.computeLuminance() > 0.85;
    final swatchBorder = isLight
        ? Border.all(color: scheme.outline.withValues(alpha: 0.55))
        : null;
    final row = Padding(
      padding: EdgeInsets.symmetric(
        horizontal: appTokens.spaceSm,
        vertical: appTokens.spaceXs,
      ),
      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              border: swatchBorder,
            ),
          ),
          SizedBox(width: appTokens.spaceSm),
          Expanded(
            child: Text(
              item.label,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ),
          Text(
            valueText,
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          if (share != null) ...[
            SizedBox(width: appTokens.spaceXs),
            Text(
              '${share.toStringAsFixed(0)}%',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ],
        ],
      ),
    );

    if (onTap == null) return row;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: appTokens.radiusMd,
        child: row,
      ),
    );
  }
}

class _TitleRow extends StatelessWidget {
  const _TitleRow({
    required this.title,
    required this.period,
    this.refreshing = false,
    this.onInfo,
  });

  final String title;
  final String period;
  final bool refreshing;
  final VoidCallback? onInfo;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              Text(
                period,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
            ],
          ),
        ),
        if (refreshing) ChartRefreshingBadge(),
        if (onInfo != null)
          IconButton(
            visualDensity: VisualDensity.compact,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            tooltip: 'Detalle y descarga',
            onPressed: onInfo,
            icon: Icon(
              Icons.info_outline_rounded,
              size: 18,
              color: scheme.onSurfaceVariant,
            ),
          ),
      ],
    );
  }
}

/// Dispatches to the right insight card by visualization / module id.
class InsightModuleCard extends StatelessWidget {
  const InsightModuleCard({
    super.key,
    required this.module,
    this.compact = false,
    this.onAction,
    this.onActionItemTap,
    this.refreshing = false,
    this.hero = false,
  });

  final AnalyticsModule module;
  final bool compact;
  final VoidCallback? onAction;
  final void Function(BreakdownItem item)? onActionItemTap;
  final bool refreshing;
  final bool hero;

  @override
  Widget build(BuildContext context) {
    if (module.id == 'action_center') {
      return ActionCenterCard(
        module: module,
        refreshing: refreshing,
        onItemTap: onActionItemTap,
      );
    }
    if (module.id == 'top_countries') {
      return CountryRankingCard(
        module: module,
        onAction: onAction,
        refreshing: refreshing,
        hero: hero,
      );
    }
    if (module.id == 'participant_readiness') {
      return DonutInsightCard(
        module: module,
        onAction: onAction,
        refreshing: refreshing,
        compact: compact,
        hero: hero,
      );
    }
    switch (module.visualization) {
      case 'line':
      case 'sparkline':
        return TrendInsightCard(
          module: module,
          compact: compact,
          onAction: onAction,
          refreshing: refreshing,
          hero: hero,
        );
      case 'donut':
        return DonutInsightCard(
          module: module,
          onAction: onAction,
          refreshing: refreshing,
          compact: compact,
          hero: hero,
        );
      case 'progress':
        return ProgressInsightCard(
          module: module,
          onAction: onAction,
          refreshing: refreshing,
          hero: hero,
        );
      case 'ranking':
      case 'bar':
        return RankingInsightCard(
          module: module,
          onAction: onAction,
          refreshing: refreshing,
          compact: compact,
          hero: hero,
        );
      case 'action_list':
        return ActionCenterCard(
          module: module,
          refreshing: refreshing,
          onItemTap: onActionItemTap,
        );
      default:
        // Prefer richer viz when payload has series/breakdown/ranking.
        if (module.series.isNotEmpty) {
          return TrendInsightCard(
            module: module,
            compact: compact,
            refreshing: refreshing,
            hero: hero,
          );
        }
        if (module.breakdown.isNotEmpty) {
          return DonutInsightCard(
            module: module,
            compact: compact,
            refreshing: refreshing,
            hero: hero,
          );
        }
        if (module.ranking.isNotEmpty) {
          return RankingInsightCard(
            module: module,
            compact: compact,
            refreshing: refreshing,
            hero: hero,
          );
        }
        return KpiInsightCard(
          module: module,
          onAction: onAction,
          refreshing: refreshing,
        );
    }
  }
}
