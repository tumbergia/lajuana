import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'app_chart_models.dart';

class AppSparkline extends StatelessWidget {
  const AppSparkline({
    super.key,
    required this.values,
    required this.semanticSummary,
    this.color,
    this.height,
  });

  final List<double> values;
  final String semanticSummary;
  final Color? color;
  final double? height;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final h = height ?? tokens.chartHeightCompact;
    if (values.isEmpty) {
      return SizedBox(height: h);
    }
    final limited = values.length > 12
        ? values.sublist(values.length - 12)
        : values;
    final c = color ?? tokens.seriesPalette.first;
    final spots = [
      for (var i = 0; i < limited.length; i++) FlSpot(i.toDouble(), limited[i]),
    ];
    final maxY = limited.fold<double>(0, (a, b) => a > b ? a : b);
    return Semantics(
      label: semanticSummary,
      child: SizedBox(
        height: h,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
          child: LineChart(
            LineChartData(
              minY: 0,
              maxY: maxY <= 0 ? 1 : maxY * 1.15,
              clipData: const FlClipData.none(),
              gridData: const FlGridData(show: false),
              borderData: FlBorderData(show: false),
              titlesData: const FlTitlesData(show: false),
              lineTouchData: const LineTouchData(enabled: false),
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: true,
                  color: c,
                  barWidth: 2.5,
                  dotData: const FlDotData(show: false),
                  belowBarData: BarAreaData(
                    show: true,
                    color: c.withValues(alpha: 0.15),
                  ),
                ),
              ],
            ),
            duration: chartAnimationOf(context),
          ),
        ),
      ),
    );
  }
}
