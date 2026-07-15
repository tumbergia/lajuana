import 'package:flutter/material.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_bar_chart.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_donut_chart.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_line_chart.dart';
import 'package:mobile/features/voice_assistant/domain/voice_chart_spec.dart';
import 'package:mobile/features/voice_assistant/presentation/helpers/voice_display_labels.dart';
import 'package:mobile_ui/mobile_ui.dart';

/// Renders an analytics [VoiceChartSpec] inline inside the voice sheet.
class VoiceChartCard extends StatelessWidget {
  const VoiceChartCard({super.key, required this.spec});

  final VoiceChartSpec spec;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.analyticsTokens;

    return Container(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
      decoration: BoxDecoration(
        color: scheme.surfaceContainer,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: scheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            spec.title,
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          if (spec.subtitle != null) ...[
            const SizedBox(height: 2),
            Text(
              spec.subtitle!,
              style: theme.textTheme.labelSmall?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
          ],
          const SizedBox(height: 8),
          _buildChart(context, tokens.chartHeightStandard),
        ],
      ),
    );
  }

  Widget _buildChart(BuildContext context, double height) {
    final summary = _semanticSummary();
    final unit = switch (spec.valueType) {
      VoiceChartValueType.currency => 'COP',
      VoiceChartValueType.percent => '%',
      VoiceChartValueType.count => '',
    };

    return switch (spec.type) {
      VoiceChartType.donut => AppDonutChart(
          points: _toPoints(spec.points),
          semanticSummary: summary,
          centerLabel: _donutCenterLabel(),
          height: height,
        ),
      VoiceChartType.line => AppLineChart(
          series: _toSeries(
            spec.series.isNotEmpty
                ? spec.series.first
                : VoiceChartSeries(label: spec.title, points: spec.points),
          ),
          semanticSummary: summary,
          height: height,
          unit: unit,
        ),
      VoiceChartType.progress || VoiceChartType.bar => AppBarChart(
          points: _toPoints(spec.points),
          semanticSummary: summary,
          height: height,
          unit: unit,
          horizontal: spec.points.length > 6,
        ),
    };
  }

  List<AppChartPoint> _toPoints(List<VoiceChartPoint> points) {
    return [
      for (final p in points)
        AppChartPoint(
          label: p.label,
          value: p.value,
          secondaryLabel: p.secondaryLabel,
          color: p.color,
        ),
    ];
  }

  AppChartSeries _toSeries(VoiceChartSeries series) {
    return AppChartSeries(
      label: series.label,
      points: _toPoints(series.points),
      color: series.color,
    );
  }

  String _semanticSummary() {
    final parts = <String>[spec.title];
    if (spec.subtitle != null) parts.add(spec.subtitle!);
    if (spec.type == VoiceChartType.line && spec.series.isNotEmpty) {
      final total = spec.series.first.points.fold<double>(
        0,
        (a, b) => a + b.value,
      );
      parts.add(_formatValue(total));
    } else if (spec.points.isNotEmpty) {
      final total = spec.points.fold<double>(0, (a, b) => a + b.value);
      parts.add(_formatValue(total));
    }
    return parts.join('. ');
  }

  String? _donutCenterLabel() {
    if (spec.points.isEmpty) return null;
    final total = spec.points.fold<double>(0, (a, b) => a + b.value);
    if (spec.valueType == VoiceChartValueType.count) {
      return total == total.roundToDouble()
          ? total.toInt().toString()
          : total.toStringAsFixed(1);
    }
    return _formatValue(total);
  }

  String _formatValue(double value) {
    return switch (spec.valueType) {
      VoiceChartValueType.currency =>
        voiceMoneyCop(value.round()).replaceFirst('Desde ', ''),
      VoiceChartValueType.percent => '${value.toStringAsFixed(1)}%',
      VoiceChartValueType.count => value == value.roundToDouble()
          ? value.toInt().toString()
          : value.toStringAsFixed(1),
    };
  }
}
