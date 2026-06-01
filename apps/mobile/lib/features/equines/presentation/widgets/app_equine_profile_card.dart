import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import '../../../../app/theme/theme_extensions.dart';
import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_metric_card.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/cards/app_selectable_card.dart';
import '../equine_labels.dart';
import '../models/equine_view_models.dart';

/// Detailed profile card for a single equine.
///
/// Displays key info in a compact, beautiful layout using [AppSelectableCard]
/// as the base. All human-readable strings come from [equine_labels].
class AppEquineProfileCard extends StatelessWidget {
  const AppEquineProfileCard({super.key, required this.detail});

  final EquineDetailRecord detail;

  @override
  Widget build(BuildContext context) {
    final d = detail;
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final theme = Theme.of(context);

    return AppSelectableCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header: name · inventory · species/breed/sex ──────────────
          _buildHeader(d, theme, scheme),
          SizedBox(height: tokens.spaceMd),

          // ── Metric row: age · weight · max load ───────────────────────
          _buildMetricRow(d, theme),
          SizedBox(height: tokens.spaceMd),

          // ── Status grid: status · location · experience ───────────────
          _buildStatusGrid(d, theme, scheme, tokens),
          SizedBox(height: tokens.spaceMd),

          // ── Footer: last service · weekly load ────────────────────────
          _buildFooter(d, theme, scheme, tokens),
        ],
      ),
    );
  }

  Widget _buildHeader(
    EquineDetailRecord d,
    ThemeData theme,
    ColorScheme scheme,
  ) {
    final subtitleParts = <String>[
      if (d.species != 'unknown') equineSpeciesLabel(d.species),
      if (d.breed != null) d.breed!,
      if (d.sex != 'unknown') equineSexLabel(d.sex),
    ];

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                d.name,
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
              ),
              if (d.inventoryNumber != null) ...[
                const SizedBox(height: 2),
                Text(
                  '#${d.inventoryNumber}',
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
                ),
              ],
            ],
          ),
        ),
        if (subtitleParts.isNotEmpty)
          Flexible(
            child: Text(
              subtitleParts.join(' · '),
              textAlign: TextAlign.end,
              style: theme.textTheme.bodySmall?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildMetricRow(EquineDetailRecord d, ThemeData theme) {
    final tokens = theme.appTokens;
    final metricPanels = <Widget>[];
    if (d.approximateAgeYears != null) {
      metricPanels.add(
        AppMetricCard(
          title: equineAgeLabel(),
          value: '${d.approximateAgeYears}',
          supportingText: equineYearsLabel(),
          compact: true,
        ),
      );
    }
    if (d.weightKg != null) {
      metricPanels.add(
        AppMetricCard(
          title: equineWeightLabelTitle(),
          value: d.weightKg!.toStringAsFixed(0),
          suffix: 'kg',
          compact: true,
          icon: Symbols.weight_rounded,
          iconSize: 56,
        ),
      );
    }
    if (d.maxRiderWeightKg != null) {
      metricPanels.add(
        AppMetricCard(
          title: equineMaxLoadLabel(),
          value: d.maxRiderWeightKg!.toStringAsFixed(0),
          suffix: 'kg',
          compact: true,
          icon: Symbols.fitness_center_rounded,
          iconSize: 56,
        ),
      );
    }
    if (metricPanels.isEmpty) return const SizedBox.shrink();

    return Column(
      children: [
        for (int i = 0; i < metricPanels.length; i++)
          Padding(
            padding: EdgeInsets.only(
              top: i == 0 ? 0 : tokens.spaceSm,
            ),
            child: metricPanels[i],
          ),
      ],
    );
  }

  Widget _buildStatusGrid(
    EquineDetailRecord d,
    ThemeData theme,
    ColorScheme scheme,
    AppThemeTokens tokens,
  ) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: equineStatusSectionLabel(),
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 8),
          _infoRow(
            context: theme,
            scheme: scheme,
            label: equineStatusFieldLabel(),
            trailing: AppBadge(
              label: d.statusLabel,
              tone: d.statusTone,
              uppercase: false,
            ),
          ),
          const SizedBox(height: 4),
          _infoRow(
            context: theme,
            scheme: scheme,
            label: equineLocationFieldLabel(),
            trailing: AppBadge(
              label: equineLocationLabel(d.locationStatus),
              tone: AppBadgeTone.neutral,
              uppercase: false,
            ),
          ),
          if (d.locationNotes != null && d.locationNotes!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Padding(
              padding: const EdgeInsets.only(left: 120),
              child: Text(
                d.locationNotes!,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
            ),
          ],
          if (d.experienceFit != null) ...[
            const SizedBox(height: 4),
            _infoRow(
              context: theme,
              scheme: scheme,
              label: equineExperienceFieldLabel(),
              trailing: AppBadge(
                label: equineExperienceLabel(d.experienceFit),
                tone: AppBadgeTone.neutral,
                uppercase: false,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildFooter(
    EquineDetailRecord d,
    ThemeData theme,
    ColorScheme scheme,
    AppThemeTokens tokens,
  ) {
    final hasLastService = d.lastServiceAt != null;
    final hasWorkload = d.workloadLast7Days > 0;
    if (!hasLastService && !hasWorkload) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: equineActivitySectionLabel(),
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 8),
          if (hasLastService)
            _infoRow(
              context: theme,
              scheme: scheme,
              label: equineLastServiceLabel(),
              value: '${d.lastServiceAt!.day.toString().padLeft(2, '0')}/${d.lastServiceAt!.month.toString().padLeft(2, '0')}/${d.lastServiceAt!.year}',
            ),
          if (hasWorkload)
            Padding(
              padding: EdgeInsets.only(top: hasLastService ? 4 : 0),
              child: _infoRow(
                context: theme,
                scheme: scheme,
                label: equineWeeklyLoadLabel(),
                value: equineServiceCountLabel(d.workloadLast7Days),
              ),
            ),
        ],
      ),
    );
  }

  Widget _infoRow({
    required ThemeData context,
    required ColorScheme scheme,
    required String label,
    String? value,
    Widget? trailing,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        SizedBox(
          width: 120,
          child: Text(
            label,
            style: context.textTheme.bodySmall?.copyWith(
              color: scheme.onSurfaceVariant,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: trailing ??
              Text(
                value ?? '',
                style: context.textTheme.bodyMedium,
              ),
        ),
      ],
    );
  }
}
