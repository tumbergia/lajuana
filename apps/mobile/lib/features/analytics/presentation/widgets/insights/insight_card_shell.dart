import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_loading_skeleton.dart';

/// Charts-first shell: title → chart hero → value/insight footer.
class InsightCardShell extends StatelessWidget {
  const InsightCardShell({
    super.key,
    required this.title,
    required this.periodLabel,
    required this.child,
    this.primaryValue,
    this.comparisonLabel,
    this.insightText,
    this.actionLabel,
    this.onAction,
    this.accentColor,
    this.refreshing = false,
    this.chartFirst = true,
    this.hero = false,
  });

  final String title;
  final String periodLabel;
  final Widget child;
  final PrimaryValue? primaryValue;
  final String? comparisonLabel;
  final String? insightText;
  final String? actionLabel;
  final VoidCallback? onAction;
  final Color? accentColor;
  final bool refreshing;
  final bool chartFirst;
  /// Emphasized home layout: larger value type, more breathing room.
  final bool hero;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;

    final header = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                      fontSize: hero ? 20 : null,
                    ),
              ),
            ),
            if (refreshing) const ChartRefreshingBadge(),
          ],
        ),
        if (periodLabel.isNotEmpty) ...[
          SizedBox(height: tokens.spaceXs),
          Text(
            periodLabel,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          ),
        ],
      ],
    );

    final valueBlock = primaryValue == null
        ? null
        : Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                primaryValue!.formatted,
                style: (hero
                        ? Theme.of(context).textTheme.headlineLarge
                        : Theme.of(context).textTheme.headlineMedium)
                    ?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(width: 8),
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  primaryValue!.unit,
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                ),
              ),
            ],
          );

    final comparison = (comparisonLabel == null || comparisonLabel!.isEmpty)
        ? null
        : Text(
            comparisonLabel!,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
          );

    final insight = (insightText == null || insightText!.isEmpty)
        ? null
        : Text(insightText!, style: Theme.of(context).textTheme.bodyMedium);

    final action = (actionLabel != null && onAction != null)
        ? AppButton(
            label: actionLabel!,
            onPressed: onAction!,
            variant: AppButtonVariant.secondary,
            expanded: true,
          )
        : null;

    final gap = hero ? tokens.spaceLg : tokens.spaceMd;

    final children = <Widget>[
      header,
      SizedBox(height: gap),
      if (chartFirst) ...[
        // Chart is the hero.
        child,
        if (valueBlock != null) ...[
          SizedBox(height: gap),
          valueBlock,
        ],
        if (comparison != null) ...[
          SizedBox(height: tokens.spaceXs),
          comparison,
        ],
      ] else ...[
        if (valueBlock != null) ...[
          valueBlock,
          SizedBox(height: tokens.spaceXs),
        ],
        if (comparison != null) ...[
          comparison,
          SizedBox(height: gap),
        ],
        child,
      ],
      if (insight != null) ...[
        SizedBox(height: gap),
        insight,
      ],
      if (action != null) ...[
        SizedBox(height: gap),
        action,
      ],
    ];

    return AppCard(
      accentColor: accentColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: children,
      ),
    );
  }
}

/// Cold-load placeholder that looks like an insight card with a chart skeleton.
class InsightCardLoadingShell extends StatelessWidget {
  const InsightCardLoadingShell({
    super.key,
    this.title = 'Cargando indicador',
    this.variant = ChartSkeletonVariant.line,
  });

  final String title;
  final ChartSkeletonVariant variant;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: scheme.onSurface.withValues(alpha: 0.55),
                ),
          ),
          SizedBox(height: tokens.spaceXs),
          Container(
            height: 12,
            width: 96,
            decoration: BoxDecoration(
              color: scheme.surfaceContainerHigh,
              borderRadius: tokens.radiusMd,
            ),
          ),
          SizedBox(height: tokens.spaceMd),
          AppChartLoadingSkeleton(variant: variant),
        ],
      ),
    );
  }
}
