import 'package:country_flags/country_flags.dart';
import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_loading_skeleton.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_donut_chart.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_line_chart.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_sparkline.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/analytics_state_views.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_card_shell.dart';

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

Widget _emptyCard(AnalyticsModule module, {required bool refreshing}) {
  return InsightCardShell(
    title: module.title,
    periodLabel: module.period.dateRangeLabel,
    insightText: module.emptyMessage ?? module.insightText,
    refreshing: refreshing,
    child: AppChartEmptyState(
      title: 'Sin datos',
      message: module.emptyMessage ?? 'Todavía no hay datos para este periodo.',
    ),
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
    final accent = tokens.domainColor(module.category);
    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _TitleRow(
            title: module.title,
            period: module.period.label,
            refreshing: refreshing,
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
    final accent = tokens.domainColor(module.category);
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
            children: [
              AnalyticsKindBadge(label: 'Tendencia', accent: accent),
              const Spacer(),
              if (refreshing) const ChartRefreshingBadge(),
            ],
          ),
          SizedBox(height: appTokens.spaceMd),
          Text(
            module.title,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
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

/// Ranking: número grande + barra gruesa, sin shell de título/valor uniforme.
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
    final scheme = Theme.of(context).colorScheme;
    if (module.isEmpty || module.ranking.isEmpty) {
      return _emptyCard(module, refreshing: refreshing);
    }
    final accent = tokens.domainColor(module.category);
    final items = module.ranking.take(hero ? 6 : 5).toList();
    final maxV =
        items.map((e) => e.rawValue).fold<double>(1, (a, b) => a > b ? a : b);

    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              AnalyticsKindBadge(
                label: 'Ranking',
                filled: true,
                accent: accent,
              ),
              const Spacer(),
              if (refreshing) const ChartRefreshingBadge(),
            ],
          ),
          SizedBox(height: Theme.of(context).appTokens.spaceMd),
          Text(
            module.title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          Text(
            module.period.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          SizedBox(height: Theme.of(context).appTokens.spaceLg),
          for (var i = 0; i < items.length; i++) ...[
            if (i > 0)
              SizedBox(height: Theme.of(context).appTokens.spaceMd + 2),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 36,
                  child: Text(
                    '${i + 1}',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w900,
                          color: tokens.seriesPalette[
                              i % tokens.seriesPalette.length],
                        ),
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              items[i].label,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context)
                                  .textTheme
                                  .bodyMedium
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                          ),
                          Text(
                            items[i].formattedValue,
                            style: Theme.of(context)
                                .textTheme
                                .titleSmall
                                ?.copyWith(fontWeight: FontWeight.w800),
                          ),
                        ],
                      ),
                      SizedBox(height: Theme.of(context).appTokens.spaceXs + 2),
                      ClipRRect(
                        borderRadius: Theme.of(context).appTokens.radiusMd,
                        child: LinearProgressIndicator(
                          value: (items[i].rawValue / maxV).clamp(0.0, 1.0),
                          minHeight: hero ? 16 : 12,
                          backgroundColor: scheme.surfaceContainerHighest,
                          color: tokens.seriesPalette[
                              i % tokens.seriesPalette.length],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
          if (module.insightText != null) ...[
            SizedBox(height: Theme.of(context).appTokens.spaceMd + 2),
            Text(module.insightText!),
          ],
        ],
      ),
    );
  }
}

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

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
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
    final shown = items.take(hero ? 6 : 4).toList();
    final accent = tokens.domainColor(module.category);

    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              AnalyticsKindBadge(label: 'Ocupación', accent: accent),
              const Spacer(),
              if (refreshing) const ChartRefreshingBadge(),
            ],
          ),
          SizedBox(height: Theme.of(context).appTokens.spaceMd),
          Text(
            module.title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          if (module.primaryValue != null) ...[
            SizedBox(height: Theme.of(context).appTokens.spaceSm),
            Text(
              '${module.primaryValue!.formatted} ${module.primaryValue!.unit}',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                    color: accent,
                  ),
            ),
          ],
          SizedBox(height: Theme.of(context).appTokens.spaceLg),
          for (var i = 0; i < shown.length; i++) ...[
            if (i > 0)
              SizedBox(
                height: hero
                    ? Theme.of(context).appTokens.spaceMd + 2
                    : Theme.of(context).appTokens.spaceMd,
              ),
            Text(
              shown[i].label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            SizedBox(height: Theme.of(context).appTokens.spaceXs + 2),
            ClipRRect(
              borderRadius: Theme.of(context).appTokens.radiusMd,
              child: LinearProgressIndicator(
                value: (shown[i].rawValue / maxV).clamp(0.0, 1.0),
                minHeight: hero ? 18 : 14,
                backgroundColor: scheme.surfaceContainerHighest,
                color: tokens.seriesPalette[i % tokens.seriesPalette.length],
              ),
            ),
            Align(
              alignment: Alignment.centerRight,
              child: Text(
                shown[i].formattedValue,
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
            ),
          ],
        ],
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

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final scheme = Theme.of(context).colorScheme;
    if (module.isEmpty || module.ranking.isEmpty) {
      return InsightCardShell(
        title: module.title,
        periodLabel: module.period.dateRangeLabel,
        insightText: module.emptyMessage ?? module.insightText,
        refreshing: refreshing,
        child: AppChartEmptyState(
          message: module.emptyMessage ??
              'Aún no hay suficientes participantes registrados para mostrar países principales.',
          icon: Icons.public,
        ),
      );
    }

    final accent = tokens.domainColor(module.category);
    final items = module.ranking.take(hero ? 6 : 5).toList();
    final maxV =
        items.map((e) => e.rawValue).fold<double>(1, (a, b) => a > b ? a : b);

    return _VizSurface(
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.public, color: accent, size: 22),
              SizedBox(width: Theme.of(context).appTokens.spaceSm),
              Expanded(
                child: Text(
                  module.title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
              if (refreshing) const ChartRefreshingBadge(),
            ],
          ),
          Text(
            module.period.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          SizedBox(height: Theme.of(context).appTokens.spaceLg),
          for (var i = 0; i < items.length; i++) ...[
            if (i > 0)
              SizedBox(
                height: hero
                    ? Theme.of(context).appTokens.spaceMd + 2
                    : Theme.of(context).appTokens.spaceMd,
              ),
            Row(
              children: [
                _Flag(code: items[i].countryCode),
                SizedBox(width: Theme.of(context).appTokens.spaceMd),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        items[i].countryName ?? items[i].label,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      SizedBox(height: Theme.of(context).appTokens.spaceXs),
                      ClipRRect(
                        borderRadius: Theme.of(context).appTokens.radiusMd,
                        child: LinearProgressIndicator(
                          value:
                              (items[i].rawValue / maxV).clamp(0.0, 1.0),
                          minHeight: hero ? 12 : 10,
                          backgroundColor: scheme.surfaceContainerHighest,
                          color: tokens.seriesPalette[
                              i % tokens.seriesPalette.length],
                        ),
                      ),
                    ],
                  ),
                ),
                SizedBox(width: Theme.of(context).appTokens.spaceMd),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      items[i].formattedValue,
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    if (items[i].sharePercentage != null)
                      Text(
                        '${items[i].sharePercentage!.toStringAsFixed(0)} %',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: scheme.onSurfaceVariant,
                            ),
                      ),
                  ],
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _Flag extends StatelessWidget {
  const _Flag({this.code});

  final String? code;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    if (code == null || code!.length != 2 || code == 'others') {
      return Icon(Icons.public, size: 32, color: scheme.onSurfaceVariant);
    }
    try {
      return ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: CountryFlag.fromCountryCode(code!, width: 36, height: 26),
      );
    } catch (_) {
      return Icon(Icons.public, size: 32, color: scheme.onSurfaceVariant);
    }
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

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final scheme = Theme.of(context).colorScheme;
    final points = chartPointsFromBreakdown(module.breakdown);
    if (module.isEmpty || points.isEmpty) {
      return _emptyCard(module, refreshing: refreshing);
    }
    final accent = tokens.domainColor(module.category);
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
          Row(
            children: [
              AnalyticsKindBadge(label: 'Distribución', accent: accent),
              const Spacer(),
              if (refreshing) const ChartRefreshingBadge(),
            ],
          ),
          SizedBox(height: Theme.of(context).appTokens.spaceMd),
          Text(
            module.title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          Text(
            module.period.label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
          SizedBox(height: Theme.of(context).appTokens.spaceMd),
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
                  ),
                ),
              ),
              SizedBox(width: Theme.of(context).appTokens.spaceMd),
              Expanded(
                flex: 4,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (var i = 0; i < points.length; i++) ...[
                      if (i > 0)
                        SizedBox(height: Theme.of(context).appTokens.spaceSm),
                      Row(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: tokens.seriesPalette[
                                  i % tokens.seriesPalette.length],
                              shape: BoxShape.circle,
                            ),
                          ),
                          SizedBox(width: Theme.of(context).appTokens.spaceSm),
                          Expanded(
                            child: Text(
                              points[i].label,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.labelMedium,
                            ),
                          ),
                          Text(
                            points[i].value == points[i].value.roundToDouble()
                                ? points[i].value.toInt().toString()
                                : points[i].value.toStringAsFixed(1),
                            style: Theme.of(context)
                                .textTheme
                                .labelLarge
                                ?.copyWith(fontWeight: FontWeight.w800),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ],
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

class _TitleRow extends StatelessWidget {
  const _TitleRow({
    required this.title,
    required this.period,
    this.refreshing = false,
  });

  final String title;
  final String period;
  final bool refreshing;

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
