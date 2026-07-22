import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/app/utils/file_saver.dart';
import 'package:mobile/features/analytics/presentation/controllers/dashboard_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/analytics_state_views.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/indicator_detail_sheet.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_module_tile.dart';

/// Nivel 2 — Analítica completa: todas las métricas del catálogo.
class AnalyticsDashboardScreen extends StatefulWidget {
  const AnalyticsDashboardScreen({super.key, required this.controller});

  final DashboardController controller;

  @override
  State<AnalyticsDashboardScreen> createState() =>
      _AnalyticsDashboardScreenState();
}

class _AnalyticsDashboardScreenState extends State<AnalyticsDashboardScreen> {
  bool _exporting = false;

  @override
  void initState() {
    super.initState();
    widget.controller.enterFullAnalytics();
    // Defer past the first build — load() notifies ModuleSlotNotifiers and
    // would otherwise trigger setState during build.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      widget.controller.load(
        showCachedFirst: true,
        allModules: true,
        silent: widget.controller.allModuleIds
            .any((id) => widget.controller.slotFor(id).hasData),
      );
    });
  }

  @override
  void dispose() {
    widget.controller.leaveFullAnalytics();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final ctrl = widget.controller;

    return AnalyticsDownloadScope(
      controller: ctrl,
      child: Scaffold(
      appBar: const AppPageAppBar(title: 'Analítica'),
      body: ListenableBuilder(
        listenable: ctrl,
        builder: (context, _) {
          final ids = ctrl.allModuleIds;
          final coldError = ctrl.state == DashboardLoadState.error &&
              !ids.any((id) => ctrl.slotFor(id).hasData);

          if (coldError) {
            return AnalyticsErrorView(
              title: 'No pudimos cargar la analítica',
              message: ctrl.error ?? 'Intenta nuevamente.',
              onRetry: () => ctrl.load(
                forceRefresh: true,
                silent: false,
                allModules: true,
              ),
            );
          }

          if (ids.isEmpty && ctrl.state != DashboardLoadState.loading) {
            return AnalyticsEmptyView(
              title: 'Sin indicadores disponibles',
              message:
                  'No hay módulos de analítica para tu rol en este momento.',
              icon: Icons.insights_outlined,
            );
          }

          return ListView.builder(
            padding: EdgeInsets.fromLTRB(
              tokens.spaceXl,
              tokens.spaceMd,
              tokens.spaceXl,
              tokens.spaceXl * 1.5,
            ),
            itemCount: ids.length + 2,
            itemBuilder: (context, index) {
              if (index == 0) {
                return Padding(
                  padding: EdgeInsets.only(bottom: tokens.spaceLg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      AppSectionHeader(
                        eyebrow: 'Panel',
                        title: 'Indicadores',
                        variant: AppSectionHeaderVariant.compact,
                      ),
                      if (ctrl.periodRangeLabel.isNotEmpty ||
                          ctrl.refreshing) ...[
                        SizedBox(height: tokens.spaceSm),
                        Text(
                          ctrl.refreshing && ctrl.periodRangeLabel.isEmpty
                              ? 'Actualizando gráficas…'
                              : ctrl.periodRangeLabel,
                          textAlign: TextAlign.center,
                          style:
                              Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .onSurfaceVariant,
                                  ),
                        ),
                      ],
                    ],
                  ),
                );
              }
              if (index == ids.length + 1) {
                return Padding(
                  padding: EdgeInsets.only(top: tokens.spaceMd),
                  child: AppButton(
                    label: _exporting
                        ? 'Preparando reporte…'
                        : 'Descargar reporte',
                    variant: AppButtonVariant.secondary,
                    onPressed: _exporting
                        ? null
                        : () async {
                            setState(() => _exporting = true);
                            try {
                              final bytes = await ctrl.downloadExport();
                              await saveFile(
                                Uint8List.fromList(bytes),
                                'analitica_${ctrl.range}.xlsx',
                                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                              );
                              if (!context.mounted) return;
                              showAppToast(
                                context,
                                message: 'Reporte descargado.',
                              );
                            } catch (_) {
                              if (!context.mounted) return;
                              showAppToast(
                                context,
                                message:
                                    'No pudimos descargar el reporte. Revisa tu conexión.',
                                isError: true,
                              );
                            } finally {
                              if (mounted) setState(() => _exporting = false);
                            }
                          },
                    expanded: true,
                  ),
                );
              }
              final id = ids[index - 1];
              return Padding(
                padding: EdgeInsets.only(bottom: tokens.spaceLg),
                child: InsightModuleTile(
                  slot: ctrl.slotFor(id),
                  moduleId: id,
                  catalog: ctrl.catalog,
                  compact: false,
                  onRetry: () => ctrl.load(
                    forceRefresh: true,
                    silent: false,
                    allModules: true,
                  ),
                ),
              );
            },
          );
        },
      ),
      ),
    );
  }
}
