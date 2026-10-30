import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'app_chart_models.dart';

class AppBarChart extends StatelessWidget {
  const AppBarChart({
    super.key,
    required this.points,
    required this.semanticSummary,
    this.horizontal = false,
    this.height,
    this.unit = '',
  });

  final List<AppChartPoint> points;
  final String semanticSummary;
  final bool horizontal;
  final double? height;
  final String unit;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final scheme = Theme.of(context).colorScheme;
    if (points.isEmpty) {
      return AppChartEmptyState(
        message: 'Todavía no hay datos para este periodo.',
      );
    }

    if (horizontal) {
      return _HorizontalBars(
        points: points,
        semanticSummary: semanticSummary,
        unit: unit,
      );
    }

    final maxY = points
        .map((p) => p.value)
        .fold<double>(0, (a, b) => a > b ? a : b);
    final chartMaxY = maxY <= 0 ? 1.0 : maxY * 1.2;
    final leftReserved = chartLeftAxisReservedSize(
      context: context,
      maxY: chartMaxY,
      style: Theme.of(
        context,
      ).textTheme.labelSmall?.copyWith(color: scheme.onSurfaceVariant),
    );
    return Semantics(
      label: semanticSummary,
      child: SizedBox(
        height: height ?? tokens.chartHeightStandard,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(0, 6, 8, 6),
          child: BarChart(
            BarChartData(
              maxY: chartMaxY,
              gridData: FlGridData(
                drawVerticalLine: false,
                getDrawingHorizontalLine: (_) =>
                    FlLine(color: tokens.gridColor, strokeWidth: 1),
              ),
              borderData: FlBorderData(show: false),
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                rightTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: leftReserved,
                    getTitlesWidget: (v, _) => chartLeftAxisTitle(
                      context: context,
                      value: v,
                      reservedSize: leftReserved,
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 36,
                    getTitlesWidget: (v, _) {
                      final i = v.toInt();
                      if (i < 0 || i >= points.length) {
                        return const SizedBox.shrink();
                      }
                      return Padding(
                        padding: const EdgeInsets.only(top: 10),
                        child: Text(
                          points[i].label,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.labelSmall
                              ?.copyWith(color: scheme.onSurfaceVariant),
                        ),
                      );
                    },
                  ),
                ),
              ),
              barTouchData: BarTouchData(
                touchTooltipData: BarTouchTooltipData(
                  getTooltipColor: (_) => tokens.tooltipBackground,
                  getTooltipItem: (group, _, rod, __) {
                    final p = points[group.x];
                    return BarTooltipItem(
                      '${p.label}\n${_fmt(rod.toY)}${unit.isEmpty ? '' : ' $unit'}',
                      TextStyle(
                        color: tokens.tooltipForeground,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    );
                  },
                ),
              ),
              barGroups: [
                for (var i = 0; i < points.length; i++)
                  BarChartGroupData(
                    x: i,
                    barRods: [
                      BarChartRodData(
                        toY: points[i].value,
                        color: tokens
                            .seriesPalette[i % tokens.seriesPalette.length],
                        width: 14,
                        borderRadius: BorderRadius.circular(tokens.barRadius),
                      ),
                    ],
                  ),
              ],
            ),
            duration: chartAnimationOf(context),
          ),
        ),
      ),
    );
  }

  static String _fmt(double v) =>
      v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(1);
}

class _HorizontalBars extends StatelessWidget {
  const _HorizontalBars({
    required this.points,
    required this.semanticSummary,
    required this.unit,
  });

  final List<AppChartPoint> points;
  final String semanticSummary;
  final String unit;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final maxV = points
        .map((p) => p.value)
        .fold<double>(1, (a, b) => a > b ? a : b);
    return Semantics(
      label: semanticSummary,
      child: Column(
        children: [
          for (var i = 0; i < points.length; i++) ...[
            if (i > 0) const SizedBox(height: 12),
            _row(
              context,
              points[i],
              maxV,
              points[i].color ??
                  tokens.seriesPalette[i % tokens.seriesPalette.length],
              tokens.barRadius + 2,
            ),
          ],
        ],
      ),
    );
  }

  Widget _row(
    BuildContext context,
    AppChartPoint point,
    double maxV,
    Color color,
    double radius,
  ) {
    final scheme = Theme.of(context).colorScheme;
    final fraction = (point.value / maxV).clamp(0.0, 1.0);
    final valueLabel =
        point.secondaryLabel ??
        '${point.value == point.value.roundToDouble() ? point.value.toInt() : point.value.toStringAsFixed(1)}'
            '${unit.isEmpty ? '' : ' $unit'}';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                point.label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
            Text(
              valueLabel,
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w800,
                color: scheme.onSurface,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(radius),
          child: SizedBox(
            height: 11,
            width: double.infinity,
            child: Stack(
              fit: StackFit.expand,
              children: [
                ColoredBox(color: scheme.surfaceContainerHighest),
                FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: fraction,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [color.withValues(alpha: 0.82), color],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
