import 'package:flutter/material.dart';

import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/controllers/dashboard_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/charts/app_chart_loading_skeleton.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/analytics_state_views.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_card_shell.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_cards.dart';

ChartSkeletonVariant skeletonForModuleId(String id) {
  switch (id) {
    case 'reservation_trend':
    case 'confirmed_value_trend':
      return ChartSkeletonVariant.line;
    case 'reservation_status':
    case 'reservation_origins':
    case 'payment_status':
    case 'equine_availability':
      return ChartSkeletonVariant.donut;
    case 'top_experiences':
    case 'top_countries':
    case 'equine_workload':
    case 'occupancy':
    case 'participant_readiness':
      return ChartSkeletonVariant.bars;
    default:
      return ChartSkeletonVariant.line;
  }
}

String loadingTitleFor(String id, List<CatalogModule> catalog) {
  for (final c in catalog) {
    if (c.id == id) return c.title;
  }
  switch (id) {
    case 'action_center':
      return 'Tareas pendientes';
    case 'reservation_trend':
      return 'Tendencia de reservas';
    case 'reservation_origins':
      return 'Orígenes de reserva';
    case 'confirmed_value_trend':
      return 'Ingresos comprometidos';
    case 'top_experiences':
      return 'Experiencias más reservadas';
    case 'top_countries':
      return 'Países de los visitantes';
    default:
      return 'Indicador';
  }
}

/// Isolates rebuilds to a single module slot.
class InsightModuleTile extends StatelessWidget {
  const InsightModuleTile({
    super.key,
    required this.slot,
    required this.moduleId,
    required this.catalog,
    this.compact = true,
    this.hero = false,
    this.onRetry,
    this.onAction,
    this.onActionItemTap,
  });

  final ModuleSlotNotifier slot;
  final String moduleId;
  final List<CatalogModule> catalog;
  final bool compact;
  final bool hero;
  final VoidCallback? onRetry;
  final VoidCallback? onAction;
  final void Function(BreakdownItem item)? onActionItemTap;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: slot,
      builder: (context, _) {
        if (slot.loading && !slot.hasData) {
          return InsightCardLoadingShell(
            title: loadingTitleFor(moduleId, catalog),
            variant: skeletonForModuleId(moduleId),
          );
        }
        if (slot.error != null && !slot.hasData) {
          return AnalyticsModuleErrorCard(
            message: slot.error!,
            onRetry: onRetry,
          );
        }
        final mod = slot.module;
        if (mod == null) return const SizedBox.shrink();

        return InsightModuleCard(
          key: ValueKey(
            '${mod.id}|${mod.period.start}|${mod.period.end}|'
            '${mod.primaryValue?.raw}|${mod.insightText}',
          ),
          module: mod,
          compact: compact && !hero,
          hero: hero,
          refreshing: false,
          onAction: onAction,
          onActionItemTap: onActionItemTap,
        );
      },
    );
  }
}
