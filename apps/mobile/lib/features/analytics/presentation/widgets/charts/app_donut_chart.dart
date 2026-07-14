import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'app_chart_models.dart';

class AppDonutChart extends StatelessWidget {
  const AppDonutChart({
    super.key,
    required this.points,
    required this.semanticSummary,
    this.centerLabel,
    this.height,
    this.showLegend = true,
    this.onSectionTap,
  });

  final List<AppChartPoint> points;
  final String semanticSummary;
  final String? centerLabel;
  final double? height;
  final bool showLegend;
  final ValueChanged<int>? onSectionTap;

  Color _colorFor(BuildContext context, int i) {
    final explicit = points[i].color;
    if (explicit != null) return explicit;
    final tokens = Theme.of(context).analyticsTokens;
    return tokens.seriesPalette[i % tokens.seriesPalette.length];
  }

  static Color _labelOn(Color background) {
    return background.computeLuminance() > 0.55
        ? const Color(0xFF1A1A1A)
        : Colors.white;
  }

  void _handleTouch(FlTouchEvent event, PieTouchResponse? response) {
    final onTap = onSectionTap;
    if (onTap == null) return;
    if (event is! FlTapUpEvent) return;
    final section = response?.touchedSection;
    if (section == null) return;
    final index = section.touchedSectionIndex;
    if (index < 0 || index >= points.length) return;
    onTap(index);
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    if (points.isEmpty) {
      return AppChartEmptyState(
        message: 'Todavía no hay datos para este periodo.',
      );
    }
    final total = points.fold<double>(0, (a, b) => a + b.value);
    final h = height ?? tokens.chartHeightStandard;
    // Leave margin so section % labels / ring aren't clipped by ClipRRect.
    final ringOuter = h * 0.42;
    final centerR = h * 0.22;
    final sectionR = ringOuter - centerR;
    return Semantics(
      label: semanticSummary,
      child: Column(
        children: [
          SizedBox(
            height: h,
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Stack(
                alignment: Alignment.center,
                clipBehavior: Clip.none,
                children: [
                  PieChart(
                    PieChartData(
                      sectionsSpace: 2,
                      centerSpaceRadius: centerR,
                      pieTouchData: PieTouchData(
                        enabled: onSectionTap != null,
                        touchCallback: _handleTouch,
                      ),
                      sections: [
                        for (var i = 0; i < points.length; i++)
                          PieChartSectionData(
                            value:
                                points[i].value <= 0 ? 0.001 : points[i].value,
                            title: points[i].value > 0 && total > 0
                                ? '${((points[i].value / total) * 100).round()}%'
                                : '',
                            color: _colorFor(context, i),
                            radius: sectionR,
                            borderSide: _colorFor(context, i)
                                        .computeLuminance() >
                                    0.85
                                ? BorderSide(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .outline
                                        .withValues(alpha: 0.55),
                                  )
                                : BorderSide.none,
                            titleStyle: Theme.of(context)
                                .textTheme
                                .labelSmall
                                ?.copyWith(
                                  color: _labelOn(_colorFor(context, i)),
                                  fontWeight: FontWeight.w700,
                                ),
                          ),
                      ],
                    ),
                    duration: chartAnimationOf(context),
                  ),
                  if (centerLabel != null)
                    IgnorePointer(
                      child: Text(
                        centerLabel!,
                        textAlign: TextAlign.center,
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                      ),
                    ),
                ],
              ),
            ),
          ),
          if (showLegend) ...[
            const SizedBox(height: 8),
            AppChartLegend(
              items: [
                for (var i = 0; i < points.length; i++)
                  (
                    label: '${points[i].label} (${_fmt(points[i].value)})',
                    color: _colorFor(context, i),
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  static String _fmt(double v) =>
      v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(1);
}
