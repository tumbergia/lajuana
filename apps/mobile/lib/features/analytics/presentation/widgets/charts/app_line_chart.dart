import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'app_chart_models.dart';

class AppLineChart extends StatelessWidget {
  const AppLineChart({
    super.key,
    required this.series,
    required this.semanticSummary,
    this.height,
    this.unit = '',
    this.hero = false,
    this.periodStart,
    this.periodEnd,
    this.periodPreset,
  });

  final AppChartSeries series;
  final String semanticSummary;
  final double? height;
  final String unit;
  /// Stronger area fill + thicker stroke for home hero modules.
  final bool hero;
  /// Analytics interval bounds — drive the independent X-axis labels
  /// and the time scale for dated spots.
  final DateTime? periodStart;
  final DateTime? periodEnd;
  /// e.g. `last_30_days` / `custom` — controls X-tick density.
  final String? periodPreset;

  /// Layout reservation under the plot. Tilted glyphs may paint past this
  /// (Stack `clipBehavior: Clip.none`) so we keep the band tight — no dead strip.
  static const _xAxisLabelHeight = 52.0;

  /// Push label anchors below the plot before applying tilt.
  static const _xAxisLabelTopInset = 41.0;

  /// Parent height bump when the label band exceeds the old titles strip.
  /// 0: band fits in the chart height budget without empty card growth.
  static const xAxisLabelBandExtra = 0.0;

  /// Matches [EdgeInsets.fromLTRB] top used around the plot Column.
  static const _chartPadTop = 6.0;

  /// ~−35° so full `dd-MM-yyyy` dates don't collide.
  static const _xLabelTilt = -0.6;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final scheme = Theme.of(context).colorScheme;
    final seeded = _seedCycleStartZero(
      points: series.points,
      periodStart: periodStart,
      periodEnd: periodEnd,
    );
    final points = seeded.points;
    if (points.isEmpty) {
      return AppChartEmptyState(message: 'Todavía no hay datos para este periodo.');
    }

    final color = series.color ?? tokens.seriesPalette.first;
    final dataMax =
        points.map((p) => p.value).fold<double>(0, (a, b) => a > b ? a : b);
    final axisBounds = chartNiceAxisBounds(dataMax);
    final chartMaxY = axisBounds.maxY;
    final yInterval = axisBounds.interval;
    final leftReserved = chartLeftAxisReservedSize(
      context: context,
      maxY: chartMaxY,
      style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: scheme.onSurfaceVariant,
          ),
    );
    final anim = chartAnimationOf(context);

    final pointDates = [for (final p in points) parseChartAxisDate(p.label)];
    final pointsAreDated = pointDates.every((d) => d != null);

    final axisStart = periodStart ??
        (pointsAreDated ? pointDates.first : null);
    final axisEnd = periodEnd ??
        (pointsAreDated ? pointDates.last : null);
    final useTimeAxis = pointsAreDated &&
        axisStart != null &&
        axisEnd != null &&
        !axisEnd.isBefore(axisStart);

    // Time scale [0, 1] for dated series so spots align with calendar labels.
    // Index scale otherwise (categorical).
    final spots = <FlSpot>[
      if (useTimeAxis)
        for (var i = 0; i < points.length; i++)
          FlSpot(
            _timeFrac(pointDates[i]!, axisStart, axisEnd),
            points[i].value,
          )
      else
        for (var i = 0; i < points.length; i++)
          FlSpot(i.toDouble(), points[i].value),
    ];

    final xTicks = _independentXTicks(
      points: points,
      periodStart: axisStart,
      periodEnd: axisEnd,
      useTimeAxis: useTimeAxis,
      periodPreset: periodPreset,
    );
    final tickAxisXs = [
      for (final t in xTicks)
        useTimeAxis
            ? t.frac
            : t.frac * (points.length - 1).clamp(1, 9999),
    ];
    // Grow by [xAxisLabelBandExtra] so the taller label band does not steal
    // plot pixels. Subtract [_chartPadTop] so plot+labels fit inside the
    // padded Column (otherwise exactly 6px yellow overflow).
    final totalHeight =
        (height ?? tokens.chartHeightStandard) + xAxisLabelBandExtra;
    final innerHeight = totalHeight - _chartPadTop;
    final plotHeight =
        (innerHeight - _xAxisLabelHeight).clamp(80.0, innerHeight);
    final labelFontSize = xTicks.length >= 10
        ? 7.0
        : xTicks.length >= 5
            ? 8.0
            : 10.0;
    final labelStyle = Theme.of(context).textTheme.labelSmall?.copyWith(
          color: scheme.onSurfaceVariant,
          fontSize: labelFontSize,
          height: 1,
        );

    return Semantics(
      label: semanticSummary,
      child: SizedBox(
        height: totalHeight,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(0, _chartPadTop, 8, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                height: plotHeight,
                child: LineChart(
                  LineChartData(
                    minX: useTimeAxis ? 0 : null,
                    maxX: useTimeAxis ? 1 : null,
                    minY: 0,
                    maxY: chartMaxY,
                    clipData: const FlClipData.all(),
                    gridData: FlGridData(
                      show: true,
                      drawVerticalLine: false,
                      horizontalInterval: yInterval,
                      getDrawingHorizontalLine: (_) => FlLine(
                        color: tokens.gridColor,
                        strokeWidth: 1,
                      ),
                    ),
                    // Vertical guides at each X-axis tick — same frac as labels.
                    extraLinesData: ExtraLinesData(
                      verticalLines: [
                        for (final x in tickAxisXs)
                          VerticalLine(
                            x: x,
                            color: tokens.gridColor.withValues(alpha: 0.55),
                            strokeWidth: 1,
                            dashArray: const [4, 3],
                          ),
                      ],
                    ),
                    borderData: FlBorderData(show: false),
                    titlesData: FlTitlesData(
                      topTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      rightTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      bottomTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      leftTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          reservedSize: leftReserved,
                          interval: yInterval,
                          getTitlesWidget: (value, _) => chartLeftAxisTitle(
                            context: context,
                            value: value,
                            reservedSize: leftReserved,
                            color: scheme.onSurfaceVariant,
                          ),
                        ),
                      ),
                    ),
                    lineTouchData: LineTouchData(
                      enabled: true,
                      touchTooltipData: LineTouchTooltipData(
                        getTooltipColor: (_) => tokens.tooltipBackground,
                        getTooltipItems: (touched) {
                          return [
                            for (final t in touched)
                              LineTooltipItem(
                                '${_tooltipLabel(
                                  points,
                                  pointDates,
                                  pointsAreDated,
                                  _nearestSpotIndex(spots, t.x),
                                )}\n'
                                '${_fmt(t.y)}${unit.isEmpty ? '' : ' $unit'}',
                                TextStyle(
                                  color: tokens.tooltipForeground,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 12,
                                ),
                              ),
                          ];
                        },
                      ),
                    ),
                    lineBarsData: [
                      LineChartBarData(
                        spots: spots,
                        isCurved: true,
                        color: color,
                        barWidth: hero
                            ? tokens.lineStrokeWidth + 1.0
                            : tokens.lineStrokeWidth,
                        dotData: FlDotData(
                          show: points.length <= 14,
                          getDotPainter: (_, __, ___, ____) =>
                              FlDotCirclePainter(
                            radius:
                                hero ? tokens.dotSize + 0.5 : tokens.dotSize,
                            color: color,
                            strokeWidth: 0,
                          ),
                        ),
                        belowBarData: BarAreaData(
                          show: true,
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [
                              color.withValues(alpha: hero ? 0.42 : 0.28),
                              color.withValues(alpha: 0.04),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                  duration: anim,
                ),
              ),
              SizedBox(
                height: _xAxisLabelHeight,
                child: Padding(
                  // Match fl_chart plot inset (leftTitles.reservedSize) and
                  // drop anchors before tilt so glyphs don't enter the plot.
                  padding: EdgeInsets.only(
                    left: leftReserved,
                    top: _xAxisLabelTopInset,
                  ),
                  child: _MappedXAxisLabels(
                    ticks: xTicks,
                    style: labelStyle,
                    tilt: _xLabelTilt,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// If the series has no point on the interval start, seed value 0 there so
  /// the line begins at the configured cycle (empty series → single zero).
  static ({List<AppChartPoint> points, bool didSeed}) _seedCycleStartZero({
    required List<AppChartPoint> points,
    required DateTime? periodStart,
    required DateTime? periodEnd,
  }) {
    if (periodStart == null) {
      return (points: points, didSeed: false);
    }
    final startDay =
        DateTime(periodStart.year, periodStart.month, periodStart.day);
    final startLabel =
        '${startDay.year}-'
        '${startDay.month.toString().padLeft(2, '0')}-'
        '${startDay.day.toString().padLeft(2, '0')}';
    final baseline = AppChartPoint(label: startLabel, value: 0);

    if (points.isEmpty) {
      if (periodEnd == null) return (points: points, didSeed: false);
      return (points: [baseline], didSeed: true);
    }

    final firstDate = parseChartAxisDate(points.first.label);
    if (firstDate == null) return (points: points, didSeed: false);
    final firstDay =
        DateTime(firstDate.year, firstDate.month, firstDate.day);
    if (firstDay.isAfter(startDay)) {
      return (points: [baseline, ...points], didSeed: true);
    }
    return (points: points, didSeed: false);
  }

  /// Fraction of [start]→[end] in [0, 1] for a calendar date.
  static double _timeFrac(DateTime date, DateTime start, DateTime end) {
    final s = DateTime(start.year, start.month, start.day);
    final e = DateTime(end.year, end.month, end.day);
    final d = DateTime(date.year, date.month, date.day);
    final span = e.difference(s).inMilliseconds;
    if (span <= 0) return 0;
    return (d.difference(s).inMilliseconds / span).clamp(0.0, 1.0);
  }

  static int _nearestSpotIndex(List<FlSpot> spots, double x) {
    var best = 0;
    var bestDist = (spots.first.x - x).abs();
    for (var i = 1; i < spots.length; i++) {
      final dist = (spots[i].x - x).abs();
      if (dist < bestDist) {
        best = i;
        bestDist = dist;
      }
    }
    return best;
  }

  /// Calendar ticks for the period (time axis) or sparse categorical labels.
  static List<_XTick> _independentXTicks({
    required List<AppChartPoint> points,
    DateTime? periodStart,
    DateTime? periodEnd,
    required bool useTimeAxis,
    String? periodPreset,
  }) {
    if (useTimeAxis && periodStart != null && periodEnd != null) {
      return [
        for (final d in rangeAxisTickDates(
          start: periodStart,
          end: periodEnd,
          preset: periodPreset,
        ))
          _XTick(
            label: formatChartAxisDate(d),
            frac: _timeFrac(d, periodStart, periodEnd),
          ),
      ];
    }

    if (points.isEmpty) return const [];
    if (points.length == 1) {
      return [_XTick(label: points.first.label, frac: 0.5)];
    }
    final step = (points.length / 4).ceil().clamp(1, points.length);
    final indices = <int>[
      for (var i = 0; i < points.length; i += step) i,
    ];
    if (indices.last != points.length - 1) {
      indices.add(points.length - 1);
    }
    final last = (points.length - 1).clamp(1, points.length);
    return [
      for (final i in indices)
        _XTick(
          label: points[i].label,
          frac: i / last,
        ),
    ];
  }

  static String _tooltipLabel(
    List<AppChartPoint> points,
    List<DateTime?> pointDates,
    bool pointsAreDated,
    int index,
  ) {
    if (index < 0 || index >= points.length) return '';
    if (pointsAreDated) {
      return formatChartAxisDate(pointDates[index]!);
    }
    return points[index].label;
  }

  static String _fmt(double v) =>
      v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(1);
}

class _XTick {
  const _XTick({required this.label, required this.frac});

  final String label;
  /// Position along the plot width in [0, 1].
  final double frac;
}

/// Places every calendar tick at its exact time fraction (not a uniform grid).
class _MappedXAxisLabels extends StatelessWidget {
  const _MappedXAxisLabels({
    required this.ticks,
    required this.style,
    required this.tilt,
  });

  final List<_XTick> ticks;
  final TextStyle? style;
  final double tilt;

  @override
  Widget build(BuildContext context) {
    if (ticks.isEmpty) return const SizedBox.shrink();

    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        // Center every label on its tick (incl. extremes). Extremes may paint
        // past the plot edge so they stay on the guide.
        const translationX = -0.5;
        return Stack(
          clipBehavior: Clip.none,
          children: [
            for (final tick in ticks)
              Positioned(
                left: tick.frac * width,
                top: 0,
                child: FractionalTranslation(
                  translation: const Offset(translationX, 0),
                  child: Transform.rotate(
                    angle: tilt,
                    alignment: Alignment.topLeft,
                    child: Text(
                      tick.label,
                      style: style,
                      maxLines: 1,
                      softWrap: false,
                      overflow: TextOverflow.visible,
                    ),
                  ),
                ),
              ),
          ],
        );
      },
    );
  }
}
