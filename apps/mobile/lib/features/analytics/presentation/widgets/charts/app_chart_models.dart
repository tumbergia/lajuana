import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

/// Chart data point used by app chart wrappers (hides fl_chart types).
@immutable
class AppChartPoint {
  const AppChartPoint({
    required this.label,
    required this.value,
    this.secondaryLabel,
  });

  final String label;
  final double value;
  final String? secondaryLabel;
}

@immutable
class AppChartSeries {
  const AppChartSeries({
    required this.label,
    required this.points,
    this.color,
  });

  final String label;
  final List<AppChartPoint> points;
  final Color? color;
}

class AppChartEmptyState extends StatelessWidget {
  const AppChartEmptyState({
    super.key,
    required this.message,
    this.icon = Icons.insights_outlined,
    this.title,
  });

  final String message;
  final IconData icon;
  final String? title;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final appTokens = Theme.of(context).appTokens;
    final chartTokens = Theme.of(context).analyticsTokens;
    return Semantics(
      label: message,
      child: SizedBox(
        height: chartTokens.chartHeightStandard,
        child: Center(
          child: Padding(
            padding: EdgeInsets.all(appTokens.spaceLg),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, color: scheme.onSurfaceVariant, size: 40),
                SizedBox(height: appTokens.spaceMd),
                if (title != null) ...[
                  Text(
                    title!,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  SizedBox(height: appTokens.spaceXs),
                ],
                Text(
                  message,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class AppChartLegend extends StatelessWidget {
  const AppChartLegend({super.key, required this.items});

  final List<({String label, Color color})> items;

  @override
  Widget build(BuildContext context) {
    final textStyle = Theme.of(context).textTheme.labelSmall;
    return Wrap(
      spacing: 12,
      runSpacing: 6,
      children: [
        for (final item in items)
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  color: item.color,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 6),
              Text(item.label, style: textStyle),
            ],
          ),
      ],
    );
  }
}

class AppChartTooltipBubble extends StatelessWidget {
  const AppChartTooltipBubble({
    super.key,
    required this.title,
    required this.valueLine,
    this.extra,
  });

  final String title;
  final String valueLine;
  final String? extra;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: tokens.tooltipBackground,
        borderRadius: BorderRadius.circular(6),
      ),
      child: DefaultTextStyle(
        style: Theme.of(context).textTheme.labelMedium!.copyWith(
              color: tokens.tooltipForeground,
            ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
            Text(valueLine),
            if (extra != null) Text(extra!),
          ],
        ),
      ),
    );
  }
}

Duration chartAnimationOf(BuildContext context) {
  if (MediaQuery.disableAnimationsOf(context)) {
    return Duration.zero;
  }
  return Theme.of(context).analyticsTokens.animationDuration;
}

/// Formats a Y-axis tick the same way [chartLeftAxisTitle] renders it.
String chartAxisTickLabel(double value) {
  if (value == 0) return '0';
  final abs = value.abs();
  if (abs >= 1000000) {
    final m = value / 1000000;
    return m == m.roundToDouble()
        ? '${m.toInt()}M'
        : '${m.toStringAsFixed(1)}M';
  }
  if (abs >= 1000) {
    final k = value / 1000;
    return k == k.roundToDouble()
        ? '${k.toInt()}k'
        : '${k.toStringAsFixed(1)}k';
  }
  if (value == value.roundToDouble()) return value.toInt().toString();
  return value.toStringAsFixed(1);
}

/// Candidate Y ticks that fl_chart is likely to paint between 0 and [maxY].
List<double> chartAxisTickSamples(double maxY) {
  if (maxY <= 0) return const [0];
  const steps = 6;
  return [
    for (var i = 0; i <= steps; i++) maxY * (i / steps),
  ];
}

/// Rounds a raw step into a "nice" 1/2/5×10ⁿ number so axis ticks land on
/// friendly values (0, 500k, 1M, 1.5M…) instead of fl_chart's default
/// interval, which can otherwise paint as few as two arbitrary labels.
double chartNiceInterval(double maxValue, {int targetTicks = 4}) {
  if (maxValue <= 0) return 1;
  final rawStep = maxValue / targetTicks;
  final magnitude =
      math.pow(10, (math.log(rawStep) / math.ln10).floor()).toDouble();
  final residual = rawStep / magnitude;
  double niceResidual;
  if (residual > 5) {
    niceResidual = 10;
  } else if (residual > 2) {
    niceResidual = 5;
  } else if (residual > 1) {
    niceResidual = 2;
  } else {
    niceResidual = 1;
  }
  return niceResidual * magnitude;
}

/// A friendly `(interval, maxY)` pair: [maxY] is a whole multiple of
/// [interval] with at least one empty step of headroom above [dataMax], so
/// every gridline lines up with a label and the top of the series never
/// touches the plot ceiling.
({double interval, double maxY}) chartNiceAxisBounds(
  double dataMax, {
  int targetTicks = 4,
}) {
  final safeMax = dataMax <= 0 ? 1.0 : dataMax;
  final interval = chartNiceInterval(safeMax, targetTicks: targetTicks);
  final steps = (safeMax / interval).ceil() + 1;
  return (interval: interval, maxY: interval * steps);
}

/// Parses the date-like labels the analytics API emits for chart series:
/// daily (`yyyy-MM-dd`), ISO week (`yyyy-Www`) and monthly (`yyyy-MM`).
/// Returns null for anything else (e.g. plain categorical labels).
DateTime? parseChartAxisDate(String label) {
  final daily = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(label);
  if (daily != null) {
    return DateTime(
      int.parse(daily.group(1)!),
      int.parse(daily.group(2)!),
      int.parse(daily.group(3)!),
    );
  }
  final week = RegExp(r'^(\d{4})-W(\d{2})$').firstMatch(label);
  if (week != null) {
    final year = int.parse(week.group(1)!);
    final weekNum = int.parse(week.group(2)!);
    // ISO week 1 is the week containing Jan 4th; weeks start on Monday.
    final jan4 = DateTime(year, 1, 4);
    final week1Monday = jan4.subtract(Duration(days: jan4.weekday - 1));
    return week1Monday.add(Duration(days: (weekNum - 1) * 7));
  }
  final month = RegExp(r'^(\d{4})-(\d{2})$').firstMatch(label);
  if (month != null) {
    return DateTime(int.parse(month.group(1)!), int.parse(month.group(2)!));
  }
  return null;
}

/// Renders a parsed axis date as `dd-MM-yyyy`, matching the format the
/// business expects to see (e.g. `15-06-2025`).
String formatChartAxisDate(DateTime date) =>
    '${date.day.toString().padLeft(2, '0')}-'
    '${date.month.toString().padLeft(2, '0')}-'
    '${date.year}';

DateTime _calendarDay(DateTime d) => DateTime(d.year, d.month, d.day);

/// Add [months] keeping the day-of-month when possible (clamps to last day
/// of shorter months: 31 Jan → 28 Feb).
DateTime addMonthsClamped(DateTime date, int months) {
  final totalMonths = date.year * 12 + (date.month - 1) + months;
  final year = totalMonths ~/ 12;
  final month = totalMonths % 12 + 1;
  final daysInMonth = DateTime(year, month + 1, 0).day;
  final day = date.day > daysInMonth ? daysInMonth : date.day;
  return DateTime(year, month, day);
}

/// Tick dates for the selected analytics range.
///
/// Labels always use the real period bounds from configuration.
///
/// - [preset] `last_30_days` or span ≤ 14 days → only [start, end]
/// - custom / other spans ≤ 45 days → weekly steps + bounds
/// - longer (trimestral / anual / custom largo) → monthly steps from [start]
List<DateTime> rangeAxisTickDates({
  required DateTime start,
  required DateTime end,
  String? preset,
}) {
  final s = _calendarDay(start);
  final e = _calendarDay(end);
  if (e.isBefore(s)) return const [];
  if (s == e) return [e];

  final spanDays = e.difference(s).inDays;
  final isMensualPreset = preset == 'last_30_days';

  // Mensual preset / muy corto: exactamente el rango elegido.
  if (spanDays <= 14 || (isMensualPreset && spanDays <= 45)) {
    return [s, e];
  }

  // Custom / rangos medios: semanal para no dejar el eje con solo 2 fechas.
  if (spanDays <= 45) {
    return _weeklyAxisTicks(s, e);
  }

  // Trimestral / anual / custom largo: un tick por mes desde el inicio.
  return _monthlyAxisTicks(s, e);
}

/// Weekly mids between [start] and [end], skipping anything too close to the end.
List<DateTime> _weeklyAxisTicks(DateTime start, DateTime end) {
  final ticks = <DateTime>{start, end};
  var cursor = start.add(const Duration(days: 7));
  while (cursor.isBefore(end)) {
    if (end.difference(cursor).inDays >= 4) {
      ticks.add(cursor);
    }
    cursor = cursor.add(const Duration(days: 7));
  }
  return ticks.toList()..sort();
}

/// Monthly mids stepping forward from [start], skipping near-duplicates of bounds.
List<DateTime> _monthlyAxisTicks(DateTime start, DateTime end) {
  final ticks = <DateTime>{start, end};
  var cursor = addMonthsClamped(start, 1);
  while (cursor.isBefore(end)) {
    if (cursor.difference(start).inDays >= 12 &&
        end.difference(cursor).inDays >= 12) {
      ticks.add(cursor);
    }
    cursor = addMonthsClamped(cursor, 1);
  }
  return ticks.toList()..sort();
}

/// Width reserved for left Y-axis labels, measured from real text layout.
///
/// Kept tight on purpose: fl_chart already carves this from the plot; extra
/// outer padding would shove the chart to the right.
double chartLeftAxisReservedSize({
  required BuildContext context,
  required double maxY,
  TextStyle? style,
}) {
  final textStyle = style ??
      Theme.of(context).textTheme.labelSmall ??
      const TextStyle(fontSize: 11);
  final scaler = MediaQuery.textScalerOf(context);
  var widest = 0.0;
  for (final tick in chartAxisTickSamples(maxY)) {
    final painter = TextPainter(
      text: TextSpan(text: chartAxisTickLabel(tick), style: textStyle),
      textDirection: TextDirection.ltr,
      textScaler: scaler,
      maxLines: 1,
    )..layout();
    if (painter.width > widest) widest = painter.width;
  }
  // Small gap between label and plot only — no double padding elsewhere.
  return (widest + 6).clamp(24.0, 56.0);
}

/// Right-aligned Y tick that fills [reservedSize] so digits are not clipped.
Widget chartLeftAxisTitle({
  required BuildContext context,
  required double value,
  required double reservedSize,
  required Color color,
}) {
  return SizedBox(
    width: reservedSize,
    child: Padding(
      padding: const EdgeInsets.only(right: 4),
      child: Text(
        chartAxisTickLabel(value),
        textAlign: TextAlign.right,
        maxLines: 1,
        softWrap: false,
        overflow: TextOverflow.visible,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: color),
      ),
    ),
  );
}

