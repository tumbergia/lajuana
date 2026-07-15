import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/app/utils/file_saver.dart';
import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/controllers/dashboard_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_donut_chart.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_line_chart.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_sparkline.dart';
import 'package:mobile/features/analytics/presentation/widgets/country_flag_colors.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/indicator_analysis.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_cards.dart';

/// Provides [DashboardController] for per-indicator downloads from insight sheets.
class AnalyticsDownloadScope extends InheritedWidget {
  const AnalyticsDownloadScope({
    super.key,
    required this.controller,
    required super.child,
  });

  final DashboardController controller;

  static DashboardController? maybeOf(BuildContext context) {
    return context
        .dependOnInheritedWidgetOfExactType<AnalyticsDownloadScope>()
        ?.controller;
  }

  @override
  bool updateShouldNotify(AnalyticsDownloadScope oldWidget) =>
      controller != oldWidget.controller;
}

/// Opens the universal indicator detail sheet (chart + table + download actions).
Future<void> showIndicatorDetailSheet(
  BuildContext context, {
  required AnalyticsModule module,
  DashboardController? controller,
}) {
  final ctrl = controller ?? AnalyticsDownloadScope.maybeOf(context);
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: false,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(
        top: Theme.of(context).appTokens.radiusXl.topLeft,
      ),
    ),
    builder: (ctx) => IndicatorDetailSheet(
      module: module,
      controller: ctrl,
    ),
  );
}

/// Detail panel for any analytics module: same chart, tabular breakdown,
/// insight text, and download actions (XLSX / PNG).
class IndicatorDetailSheet extends StatefulWidget {
  const IndicatorDetailSheet({
    super.key,
    required this.module,
    this.controller,
  });

  final AnalyticsModule module;
  final DashboardController? controller;

  @override
  State<IndicatorDetailSheet> createState() => _IndicatorDetailSheetState();
}

class _IndicatorDetailSheetState extends State<IndicatorDetailSheet> {
  final GlobalKey _chartKey = GlobalKey();
  bool _busyXlsx = false;
  bool _busyPng = false;

  AnalyticsModule get module => widget.module;

  Future<void> _downloadXlsx() async {
    final ctrl = widget.controller ?? AnalyticsDownloadScope.maybeOf(context);
    if (ctrl == null) {
      showAppToast(
        context,
        message: 'No hay conexión de descarga disponible.',
        isError: true,
      );
      return;
    }
    setState(() => _busyXlsx = true);
    try {
      final bytes = await ctrl.downloadExport(moduleIds: [module.id]);
      final safe = module.id.replaceAll(RegExp(r'[^a-zA-Z0-9_-]'), '_');
      await saveFile(
        Uint8List.fromList(bytes),
        'indicador_$safe.xlsx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      );
      if (!mounted) return;
      showAppToast(context, message: 'Indicador descargado (Excel).');
    } catch (_) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No pudimos descargar el Excel. Revisa tu conexión.',
        isError: true,
      );
    } finally {
      if (mounted) setState(() => _busyXlsx = false);
    }
  }

  Future<void> _downloadPng() async {
    setState(() => _busyPng = true);
    try {
      final boundary = _chartKey.currentContext?.findRenderObject()
          as RenderRepaintBoundary?;
      if (boundary == null) {
        throw StateError('chart boundary missing');
      }
      final image = await boundary.toImage(pixelRatio: 3);
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      if (byteData == null) throw StateError('png encode failed');
      final safe = module.id.replaceAll(RegExp(r'[^a-zA-Z0-9_-]'), '_');
      await saveFile(
        byteData.buffer.asUint8List(),
        'indicador_$safe.png',
        'image/png',
      );
      if (!mounted) return;
      showAppToast(context, message: 'Gráfica descargada (PNG).');
    } catch (_) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No pudimos capturar la gráfica.',
        isError: true,
      );
    } finally {
      if (mounted) setState(() => _busyPng = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final bottomInset = MediaQuery.viewPaddingOf(context).bottom;
    final description = module.description.trim();
    final insight = module.insightText?.trim();
    final accent = chromeAccentForModule(context, module);
    final maxHeight = MediaQuery.sizeOf(context).height * 0.92;

    return SafeArea(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: maxHeight),
        child: SingleChildScrollView(
          padding: EdgeInsets.fromLTRB(
            tokens.spaceXl,
            tokens.spaceLg,
            tokens.spaceXl,
            tokens.spaceXl + bottomInset,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                    borderRadius: tokens.radiusSm,
                  ),
                ),
              ),
              SizedBox(height: tokens.spaceXl),
              Text(
                module.title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              SizedBox(height: tokens.spaceXs),
              Text(
                module.period.dateRangeLabel.isNotEmpty
                    ? module.period.dateRangeLabel
                    : module.period.label,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
              if (description.isNotEmpty) ...[
                SizedBox(height: tokens.spaceMd),
                Text(
                  description,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                ),
              ],
              if (module.primaryValue != null) ...[
                SizedBox(height: tokens.spaceLg),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      module.primaryValue!.formatted,
                      style: Theme.of(context)
                          .textTheme
                          .headlineMedium
                          ?.copyWith(
                            fontWeight: FontWeight.w900,
                            color: accent,
                          ),
                    ),
                    SizedBox(width: tokens.spaceSm),
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
              SizedBox(height: tokens.spaceLg),
              RepaintBoundary(
                key: _chartKey,
                child: ColoredBox(
                  color: scheme.surface,
                  child: Padding(
                    padding: EdgeInsets.all(tokens.spaceSm),
                    child: _DetailChart(module: module, accent: accent),
                  ),
                ),
              ),
              if (insight != null && insight.isNotEmpty) ...[
                SizedBox(height: tokens.spaceLg),
                Container(
                  padding: EdgeInsets.all(tokens.spaceMd),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: 0.10),
                    borderRadius: tokens.radiusMd,
                    border: Border.all(color: accent.withValues(alpha: 0.24)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.lightbulb_outline_rounded,
                        size: 18,
                        color: accent,
                      ),
                      SizedBox(width: tokens.spaceSm),
                      Expanded(
                        child: Text(
                          insight,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              ..._buildAnalysisSections(context, accent),
              SizedBox(height: tokens.spaceLg),
              Text(
                'Desglose',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              SizedBox(height: tokens.spaceMd),
              _DetailTable(module: module, accent: accent),
              SizedBox(height: tokens.spaceXl),
              Text(
                'Descargar',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              SizedBox(height: tokens.spaceSm),
              Text(
                'Excel incluye la gráfica nativa, la tabla, parámetros y el análisis. '
                'PNG captura la gráfica tal como se ve aquí.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
              SizedBox(height: tokens.spaceMd),
              AppButton(
                label: _busyXlsx ? 'Preparando Excel…' : 'Descargar Excel',
                variant: AppButtonVariant.primary,
                onPressed: _busyXlsx || _busyPng ? null : _downloadXlsx,
                expanded: true,
                icon: Icons.table_view_rounded,
              ),
              SizedBox(height: tokens.spaceSm),
              AppButton(
                label: _busyPng ? 'Capturando…' : 'Descargar PNG',
                variant: AppButtonVariant.secondary,
                onPressed: _busyXlsx || _busyPng ? null : _downloadPng,
                expanded: true,
                icon: Icons.image_outlined,
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildAnalysisSections(BuildContext context, Color accent) {
    final tokens = Theme.of(context).appTokens;
    final scheme = Theme.of(context).colorScheme;
    final params = indicatorParameterRows(module);
    final analysis = buildIndicatorAnalysis(module)
        .where((line) => line != module.insightText?.trim())
        .toList();
    final widgets = <Widget>[];

    if (params.isNotEmpty) {
      widgets.add(SizedBox(height: tokens.spaceLg));
      widgets.add(
        Text(
          'Parámetros',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
      );
      widgets.add(SizedBox(height: tokens.spaceMd));
      widgets.add(
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: scheme.outlineVariant),
            borderRadius: tokens.radiusMd,
          ),
          child: Column(
            children: [
              for (var i = 0; i < params.length; i++) ...[
                if (i > 0)
                  Divider(height: 1, color: scheme.outlineVariant),
                Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: tokens.spaceMd,
                    vertical: tokens.spaceSm,
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          params[i].key,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: scheme.onSurfaceVariant,
                              ),
                        ),
                      ),
                      Text(
                        params[i].value,
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      );
    }

    if (analysis.isNotEmpty) {
      widgets.add(SizedBox(height: tokens.spaceLg));
      widgets.add(
        Text(
          'Análisis',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
      );
      widgets.add(SizedBox(height: tokens.spaceMd));
      for (final line in analysis) {
        widgets.add(
          Padding(
            padding: EdgeInsets.only(bottom: tokens.spaceSm),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Icon(Icons.circle, size: 6, color: accent),
                ),
                SizedBox(width: tokens.spaceSm),
                Expanded(
                  child: Text(
                    line,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
        );
      }
    }

    return widgets;
  }
}

class _DetailChart extends StatelessWidget {
  const _DetailChart({required this.module, required this.accent});

  final AnalyticsModule module;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final scheme = Theme.of(context).colorScheme;
    final viz = module.visualization;

    if (module.series.isNotEmpty &&
        (viz == 'line' || viz == 'sparkline' || viz == 'kpi')) {
      final series = module.series.first;
      final points = chartPointsFromSeries(series);
      return SizedBox(
        height: tokens.chartHeightWide + AppLineChart.xAxisLabelBandExtra,
        child: AppLineChart(
          series: AppChartSeries(
            label: series.label,
            points: points,
            color: accent,
          ),
          semanticSummary: module.insightText ?? module.title,
          unit: series.unit,
          height: tokens.chartHeightWide,
          hero: true,
          periodStart: DateTime.tryParse(module.period.start),
          periodEnd: DateTime.tryParse(module.period.end),
          periodPreset: module.period.preset,
        ),
      );
    }

    if (module.id == 'top_countries' && module.ranking.isNotEmpty) {
      final items = module.ranking;
      final total = items.fold<double>(0, (s, i) => s + i.rawValue);
      final points = [
        for (final item in items)
          AppChartPoint(
            label: item.countryName ?? item.label,
            value: item.rawValue,
            color: countryFlagColor(
              item.countryCode,
              fallback: scheme.outline,
            ),
          ),
      ];
      return AppDonutChart(
        points: points,
        semanticSummary: module.insightText ?? module.title,
        centerLabel: total == total.roundToDouble()
            ? '${total.toInt()}'
            : total.toStringAsFixed(0),
        height: tokens.chartHeightWide,
        showLegend: true,
      );
    }

    if (module.breakdown.isNotEmpty &&
        (viz == 'donut' ||
            module.id == 'participant_readiness' ||
            module.id == 'action_center' ||
            module.id == 'equine_care_alerts')) {
      if (viz == 'donut' || module.id == 'participant_readiness') {
        final items = module.breakdown;
        final points = [
          for (var i = 0; i < items.length; i++)
            AppChartPoint(
              label: items[i].label,
              value: items[i].rawValue,
              color: breakdownItemColor(context, module, items[i], i),
            ),
        ];
        return AppDonutChart(
          points: points,
          semanticSummary: module.insightText ?? module.title,
          centerLabel: module.primaryValue?.formatted,
          height: tokens.chartHeightWide,
          showLegend: true,
        );
      }
      // Action lists: compact spark of counts
      return AppSparkline(
        values: module.breakdown.map((b) => b.rawValue).toList(),
        semanticSummary: module.insightText ?? module.title,
        color: accent,
        height: tokens.chartHeightCompact,
      );
    }

    if (module.ranking.isNotEmpty ||
        viz == 'ranking' ||
        viz == 'progress' ||
        viz == 'bar') {
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
      if (items.isEmpty) {
        return Text(
          module.emptyMessage ?? 'Sin datos para graficar.',
          style: Theme.of(context).textTheme.bodyMedium,
        );
      }
      final maxV =
          items.map((e) => e.rawValue).fold<double>(1, (a, b) => a > b ? a : b);
      final isOccupancy = module.id == 'occupancy';
      return Column(
        children: [
          for (var i = 0; i < items.length; i++) ...[
            if (i > 0) SizedBox(height: Theme.of(context).appTokens.spaceMd),
            _SheetBarRow(
              label: items[i].label,
              valueText: items[i].formattedValue,
              share: items[i].sharePercentage,
              fraction: isOccupancy && items[i].sharePercentage != null
                  ? (items[i].sharePercentage! / 100).clamp(0.0, 1.0)
                  : (items[i].rawValue / maxV).clamp(0.0, 1.0),
              color: isOccupancy
                  ? _occupancyColor(tokens, items[i].sharePercentage)
                  : (module.id == 'top_experiences'
                      ? _experiencesPalette[i % _experiencesPalette.length]
                      : tokens.seriesPalette[i % tokens.seriesPalette.length]),
            ),
          ],
        ],
      );
    }

    if (module.series.isNotEmpty) {
      final series = module.series.first;
      return SizedBox(
        height: tokens.chartHeightWide + AppLineChart.xAxisLabelBandExtra,
        child: AppLineChart(
          series: AppChartSeries(
            label: series.label,
            points: chartPointsFromSeries(series),
            color: accent,
          ),
          semanticSummary: module.insightText ?? module.title,
          unit: series.unit,
          height: tokens.chartHeightWide,
          hero: true,
        ),
      );
    }

    return Text(
      module.emptyMessage ?? 'Sin gráfica para este indicador.',
      style: Theme.of(context).textTheme.bodyMedium,
    );
  }
}

const List<Color> _experiencesPalette = [
  Color(0xFF00E676),
  Color(0xFFFF9100),
  Color(0xFF40C4FF),
  Color(0xFFE040FB),
  Color(0xFFFFEA00),
  Color(0xFF7C4DFF),
];

Color _occupancyColor(AnalyticsVisualTokens tokens, double? share) {
  if (share == null) return tokens.neutral;
  if (share < 25) return tokens.danger;
  if (share < 75) return tokens.warning;
  return tokens.success;
}

class _SheetBarRow extends StatelessWidget {
  const _SheetBarRow({
    required this.label,
    required this.valueText,
    required this.fraction,
    required this.color,
    this.share,
  });

  final String label;
  final String valueText;
  final double fraction;
  final Color color;
  final double? share;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final analytics = Theme.of(context).analyticsTokens;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
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
              SizedBox(width: tokens.spaceSm),
              Text(
                '${share!.toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
            ],
          ],
        ),
        SizedBox(height: tokens.spaceXs),
        ClipRRect(
          borderRadius: BorderRadius.circular(analytics.barRadius + 2),
          child: SizedBox(
            height: 12,
            width: double.infinity,
            child: Stack(
              fit: StackFit.expand,
              children: [
                ColoredBox(color: scheme.surfaceContainerHighest),
                FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: fraction.clamp(0.0, 1.0),
                  child: ColoredBox(color: color),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _DetailTable extends StatelessWidget {
  const _DetailTable({required this.module, required this.accent});

  final AnalyticsModule module;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;

    if (module.series.isNotEmpty &&
        module.breakdown.isEmpty &&
        module.ranking.isEmpty) {
      final series = module.series.first;
      return Column(
        children: [
          for (final p in series.points)
            Padding(
              padding: EdgeInsets.only(bottom: tokens.spaceSm),
              child: Row(
                children: [
                  Expanded(child: Text(p.label)),
                  Text(
                    '${p.raw % 1 == 0 ? p.raw.toInt() : p.raw} ${p.unit.isNotEmpty ? p.unit : series.unit}',
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ],
              ),
            ),
        ],
      );
    }

    if (module.breakdown.isNotEmpty) {
      return Column(
        children: [
          for (var i = 0; i < module.breakdown.length; i++)
            Padding(
              padding: EdgeInsets.only(bottom: tokens.spaceSm),
              child: Row(
                children: [
                  Container(
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                      color: breakdownItemColor(
                        context,
                        module,
                        module.breakdown[i],
                        i,
                      ),
                      shape: BoxShape.circle,
                    ),
                  ),
                  SizedBox(width: tokens.spaceSm),
                  Expanded(child: Text(module.breakdown[i].label)),
                  Text(
                    module.breakdown[i].formattedValue,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  if (module.breakdown[i].sharePercentage != null) ...[
                    SizedBox(width: tokens.spaceSm),
                    SizedBox(
                      width: 44,
                      child: Text(
                        '${module.breakdown[i].sharePercentage!.toStringAsFixed(0)}%',
                        textAlign: TextAlign.end,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: scheme.onSurfaceVariant,
                            ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
        ],
      );
    }

    if (module.ranking.isNotEmpty) {
      return Column(
        children: [
          for (var i = 0; i < module.ranking.length; i++)
            Padding(
              padding: EdgeInsets.only(bottom: tokens.spaceSm),
              child: Row(
                children: [
                  SizedBox(
                    width: 28,
                    child: Text(
                      '#${module.ranking[i].rank}',
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            color: scheme.onSurfaceVariant,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                  ),
                  Expanded(child: Text(module.ranking[i].label)),
                  Text(
                    module.ranking[i].formattedValue,
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  if (module.ranking[i].sharePercentage != null) ...[
                    SizedBox(width: tokens.spaceSm),
                    SizedBox(
                      width: 44,
                      child: Text(
                        '${module.ranking[i].sharePercentage!.toStringAsFixed(0)}%',
                        textAlign: TextAlign.end,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: scheme.onSurfaceVariant,
                            ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
        ],
      );
    }

    return Text(
      'Sin filas tabulares.',
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: scheme.onSurfaceVariant,
          ),
    );
  }
}
