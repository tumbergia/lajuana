import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/data/analytics_repository.dart';
import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/analytics/presentation/controllers/dashboard_controller.dart';
import 'package:mobile/features/analytics/presentation/screens/action_pending_list_screen.dart';
import 'package:mobile/features/analytics/presentation/screens/analytics_dashboard_screen.dart';
import 'package:mobile/features/analytics/presentation/screens/configure_analytics_screen.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/analytics_interval_sheet.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/analytics_state_views.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/indicator_detail_sheet.dart';
import 'package:mobile/features/analytics/presentation/widgets/insights/insight_module_tile.dart';
import 'package:mobile/features/analytics/remote/analytics_api_client.dart';
import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';

/// Inicio (Nivel 1) — charts-first; carga inicial con un solo loader.
class AnalyticsHomeScreen extends StatefulWidget {
  const AnalyticsHomeScreen({
    super.key,
    required this.analyticsApiClient,
    this.userDisplayName,
    this.userKey = 'default',
    this.reservationsModule,
    this.authController,
    this.catalogsModule,
    this.assignmentsModule,
    this.equineRepository,
    this.equineEventRepository,
  });

  final AnalyticsApiClient analyticsApiClient;
  final String? userDisplayName;
  final String userKey;
  final ReservationsModule? reservationsModule;
  final AuthController? authController;
  final CatalogsModule? catalogsModule;
  final AssignmentsModule? assignmentsModule;
  final EquineRepository? equineRepository;
  final EquineEventRepository? equineEventRepository;

  @override
  State<AnalyticsHomeScreen> createState() => _AnalyticsHomeScreenState();
}

class _AnalyticsHomeScreenState extends State<AnalyticsHomeScreen>
    with RefreshableState {
  late final DashboardController _controller;

  @override
  void initState() {
    super.initState();
    _controller = DashboardController(
      repository: AnalyticsRepository(
        apiClient: widget.analyticsApiClient,
        userKey: widget.userKey,
      ),
    );
    _controller.bootstrap();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Future<void> onRefresh() =>
      _controller.load(forceRefresh: true, silent: true);

  String get _greetingName {
    final raw = widget.userDisplayName?.trim() ?? '';
    if (raw.isEmpty) return 'equipo';
    return raw.split(RegExp(r'\s+')).first;
  }

  static const _presetRanges = [
    AppSegmentedFilterItem(label: 'Mensual', value: 'last_30_days'),
    AppSegmentedFilterItem(label: 'Trimestral', value: 'last_3_months'),
    AppSegmentedFilterItem(label: 'Anual', value: 'this_year'),
  ];

  static String _shortRangeLabel(DateTime from, DateTime to) {
    String d(DateTime x) =>
        '${x.day.toString().padLeft(2, '0')}/${x.month.toString().padLeft(2, '0')}';
    if (from.year == to.year && from.month == to.month && from.day == to.day) {
      return d(from);
    }
    return '${d(from)}–${d(to)}';
  }

  Future<void> _onPresetChanged(String? value) async {
    if (value == null) return;
    await _controller.setRange(value);
  }

  Future<void> _pickCustomRange() async {
    final picked = await showAnalyticsIntervalSheet(
      context,
      initialFrom: _controller.customFrom,
      initialTo: _controller.customTo,
    );
    if (picked == null || !mounted) return;
    await _controller.setCustomRange(picked.start, picked.end);
  }

  void _openActionItem(BreakdownItem item) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ActionPendingListScreen(
          item: item,
          reservationsModule: widget.reservationsModule,
          authController: widget.authController,
          catalogsModule: widget.catalogsModule,
          assignmentsModule: widget.assignmentsModule,
          equineRepository: widget.equineRepository,
          equineEventRepository: widget.equineEventRepository,
          userRole: widget.authController?.currentUser?.role,
        ),
      ),
    );
  }

  Widget _buildRangeControls(DashboardController ctrl) {
    final tokens = Theme.of(context).appTokens;
    final scheme = Theme.of(context).colorScheme;
    final customActive = ctrl.hasCustomRange;

    return Row(
      children: [
        Expanded(
          child: AppSegmentedFilter<String>(
            items: _presetRanges,
            value: customActive ? null : ctrl.range,
            allowDeselect: false,
            onChanged: _onPresetChanged,
          ),
        ),
        SizedBox(width: tokens.spaceSm),
        Tooltip(
          message: customActive
              ? 'Intervalo ${_shortRangeLabel(ctrl.customFrom!, ctrl.customTo!)}'
              : 'Definir intervalo',
          child: Material(
            color: customActive
                ? scheme.surfaceContainerHighest
                : scheme.surfaceContainerLow,
            borderRadius: BorderRadius.circular(4),
            child: InkWell(
              borderRadius: BorderRadius.circular(4),
              onTap: _pickCustomRange,
              child: SizedBox(
                height: 44,
                width: customActive ? null : 44,
                child: Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: customActive ? tokens.spaceMd : 0,
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.date_range_rounded,
                        size: 20,
                        color: customActive
                            ? scheme.onSurface
                            : scheme.onSurfaceVariant,
                      ),
                      if (customActive) ...[
                        SizedBox(width: tokens.spaceXs),
                        Text(
                          _shortRangeLabel(
                            ctrl.customFrom!,
                            ctrl.customTo!,
                          ).toUpperCase(),
                          style:
                              Theme.of(context).textTheme.labelSmall?.copyWith(
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 0.4,
                                  ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _openConfigure() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ConfigureAnalyticsScreen(controller: _controller),
      ),
    );
  }

  void _openDashboard() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AnalyticsDashboardScreen(controller: _controller),
      ),
    );
  }

  bool _isCold(DashboardController ctrl) {
    return ctrl.state == DashboardLoadState.loading &&
        !ctrl.homeModuleIds.any((id) => ctrl.slotFor(id).hasData) &&
        !ctrl.slotFor('action_center').hasData;
  }

  /// Carga inicial o cambio de intervalo: un solo loader, sin cards.
  bool _isAnalyzing(DashboardController ctrl) {
    return ctrl.blockingUi || _isCold(ctrl);
  }

  bool _isFullError(DashboardController ctrl) {
    return ctrl.state == DashboardLoadState.error &&
        !ctrl.homeModuleIds.any((id) => ctrl.slotFor(id).hasData) &&
        !(ctrl.slotFor('action_center').hasData);
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;

    return AnalyticsDownloadScope(
      controller: _controller,
      child: Padding(
      padding: EdgeInsets.fromLTRB(
        tokens.spaceXl,
        tokens.spaceXl,
        tokens.spaceXl,
        tokens.spaceXl,
      ),
      child: ListenableBuilder(
        listenable: _controller,
        builder: (context, _) {
          final analyzing = _isAnalyzing(_controller);
          final fullError = _isFullError(_controller);
          return CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Builder(
                  builder: (context) {
                    final scheme = Theme.of(context).colorScheme;
                    final period = _periodCaption(_controller);
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        AppSectionHeader(
                          eyebrow: 'Hola',
                          title: _greetingName,
                        ),
                        if (period.isNotEmpty) ...[
                          SizedBox(height: tokens.spaceSm),
                          Text(
                            period,
                            textAlign: TextAlign.center,
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium
                                ?.copyWith(
                                  color: scheme.onSurfaceVariant,
                                ),
                          ),
                        ],
                      ],
                    );
                  },
                ),
              ),
              SliverToBoxAdapter(child: SizedBox(height: tokens.spaceLg)),
              SliverToBoxAdapter(
                child: fullError
                    ? AnalyticsErrorView(
                        title: 'No pudimos cargar la analítica',
                        message:
                            _controller.error ?? 'Intenta nuevamente.',
                        onRetry: () => _controller.load(
                          forceRefresh: true,
                          silent: false,
                        ),
                      )
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          if (_controller.error != null &&
                              !fullError &&
                              !_controller.isOffline) ...[
                            AppStatusBanner(
                              title: 'Error de sincronización',
                              message: _controller.error!,
                              tone: AppStatusBannerTone.danger,
                              icon: Icons.error_outline_rounded,
                              badgeLabel: 'Error',
                              onTap: () => _controller.load(
                                forceRefresh: true,
                                silent: false,
                              ),
                            ),
                            SizedBox(height: tokens.spaceMd),
                          ],
                          _buildRangeControls(_controller),
                        ],
                      ),
              ),
              if (analyzing)
                SliverFillRemaining(
                  hasScrollBody: false,
                  child: Builder(
                    builder: (context) {
                      final scheme = Theme.of(context).colorScheme;
                      return Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const AppCenteredLoader(fill: false),
                            SizedBox(height: tokens.spaceLg),
                            Text(
                              'Analizando indicadores…',
                              textAlign: TextAlign.center,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                  ),
                            ),
                            SizedBox(height: tokens.spaceSm),
                            Text(
                              'Un momento',
                              textAlign: TextAlign.center,
                              style: Theme.of(context)
                                  .textTheme
                                  .bodySmall
                                  ?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                  ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                )
              else if (!fullError) ...[
                SliverToBoxAdapter(
                  child: ListenableBuilder(
                    listenable: _controller.slotFor('action_center'),
                    builder: (context, _) {
                      final slot = _controller.slotFor('action_center');
                      final mod = slot.module;
                      if (!slot.loading && (mod == null || mod.isEmpty)) {
                        return const SizedBox.shrink();
                      }
                      return Padding(
                        padding: EdgeInsets.only(
                          top: tokens.spaceLg,
                          bottom: tokens.spaceLg,
                        ),
                        child: InsightModuleTile(
                          slot: slot,
                          moduleId: 'action_center',
                          catalog: _controller.catalog,
                          compact: false,
                          onRetry: () => _controller.load(
                            forceRefresh: true,
                            silent: false,
                          ),
                          onActionItemTap: _openActionItem,
                        ),
                      );
                    },
                  ),
                ),
                SliverToBoxAdapter(
                  child: Builder(
                    builder: (context) {
                      final ids = _controller.homeModuleIds;
                      if (ids.isEmpty) {
                        return Padding(
                          padding: EdgeInsets.only(bottom: tokens.spaceLg),
                          child: AnalyticsEmptyView(
                            title: 'Sin indicadores en Inicio',
                            message:
                                'Elige indicadores para ver gráficas aquí.',
                            actionLabel: 'Configurar indicadores',
                            onAction: _openConfigure,
                          ),
                        );
                      }
                      return Column(
                        children: [
                          for (var i = 0; i < ids.length; i++)
                            Padding(
                              padding:
                                  EdgeInsets.only(bottom: tokens.spaceLg),
                              child: InsightModuleTile(
                                slot: _controller.slotFor(ids[i]),
                                moduleId: ids[i],
                                catalog: _controller.catalog,
                                compact: i != 0,
                                hero: i == 0,
                                onRetry: () => _controller.load(
                                  forceRefresh: true,
                                  silent: false,
                                ),
                              ),
                            ),
                        ],
                      );
                    },
                  ),
                ),
                SliverToBoxAdapter(
                  child: Column(
                    children: [
                      AppButton(
                        label: 'Ver analítica completa',
                        onPressed: _openDashboard,
                        expanded: true,
                      ),
                      SizedBox(height: tokens.spaceMd),
                      AppButton(
                        label: 'Configurar indicadores',
                        variant: AppButtonVariant.secondary,
                        onPressed: _openConfigure,
                        expanded: true,
                      ),
                      SizedBox(height: tokens.spaceXl),
                    ],
                  ),
                ),
              ],
            ],
          );
        },
      ),
      ),
    );
  }

  String _periodCaption(DashboardController ctrl) {
    if (_isAnalyzing(ctrl)) return '';
    if (ctrl.periodRangeLabel.isNotEmpty) return ctrl.periodRangeLabel;
    if (ctrl.refreshing) return 'Actualizando gráficas…';
    return '';
  }
}
