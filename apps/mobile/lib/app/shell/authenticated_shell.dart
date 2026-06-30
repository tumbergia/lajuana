import 'dart:async' show unawaited;

import 'package:flutter/material.dart';

import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_api_client.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/app/navigation/shell_navigation_controller.dart';
import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';
import 'package:mobile_ui/src/widgets/app_top_bar.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'widgets/shell_status_region.dart';
import 'package:mobile/features/configuration/presentation/screens/more_flow_screen.dart';
import 'package:mobile/features/dashboard/presentation/screens/dashboard_screen.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile/features/catalogs/experiences/presentation/screens/experiences_module_screen.dart';
import 'package:mobile/features/equines/presentation/screens/equines_module_screen.dart';
import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/reservations/presentation/screens/reservations_module_screen.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/features/saddles/saddles_module.dart';
import 'package:mobile/features/providers/providers_module.dart';

class AuthenticatedShell extends StatefulWidget {
  const AuthenticatedShell({
    super.key,
    required this.authController,
    required this.contactsApiClient,
    this.catalogsModule,
    this.reservationsModule,
    this.saddlesModule,
    this.providersModule,
    this.assignmentsModule,
    required this.equineRepository,
    required this.equineEventRepository,
    this.outbox,
    this.onCallRequested,
  });

  final AuthController authController;
  final AuthApiClient contactsApiClient;
  final CatalogsModule? catalogsModule;
  final ReservationsModule? reservationsModule;
  final SaddlesModule? saddlesModule;
  final ProvidersModule? providersModule;
  final AssignmentsModule? assignmentsModule;
  final OutboxRepository? outbox;
  final EquineRepository equineRepository;
  final EquineEventRepository equineEventRepository;
  final Future<bool> Function(String phone)? onCallRequested;

  @override
  State<AuthenticatedShell> createState() => _AuthenticatedShellState();
}

class _AuthenticatedShellState extends State<AuthenticatedShell> {
  late final ShellNavigationController _shellNav;
  final Map<AppNavItem, GlobalKey<NavigatorState>> _navigatorKeys = {};
  final Set<AppNavItem> _visitedTabs = {};
  bool _wasBackendReachable = false;

  @override
  void initState() {
    super.initState();
    _shellNav = ShellNavigationController();
    _ensureTab(AppNavItem.inicio);
  }

  @override
  void dispose() {
    _shellNav.dispose();
    super.dispose();
  }

  void _ensureTab(AppNavItem tab) {
    if (tab == AppNavItem.none) return;
    _visitedTabs.add(tab);
    _navigatorKeys.putIfAbsent(tab, () => GlobalKey<NavigatorState>());
  }

  void _onBottomNavTap(AppNavItem item) {
    if (item == AppNavItem.none) return;
    if (item != AppNavItem.mas) {
      // Sub-destinos de Mas se conservan al reentrar al mismo tab.
    }
    _ensureTab(item);
    _shellNav.selectTab(item);
    setState(() {});
  }

  Widget _tabRoot(AppNavItem tab) {
    switch (tab) {
      case AppNavItem.inicio:
        return DashboardScreen(
          authController: widget.authController,
          onNavigateToTab: _onBottomNavTap,
        );
      case AppNavItem.reservas:
        return ReservationsModuleScreen(
          catalogsModule: widget.catalogsModule,
          authController: widget.authController,
          reservationsModule: widget.reservationsModule,
          assignmentsModule: widget.assignmentsModule,
        );
      case AppNavItem.equinos:
        return EquinesModuleScreen(
          repository: widget.equineRepository,
          eventRepository: widget.equineEventRepository,
          userRole: widget.authController.currentUser?.role,
        );
      case AppNavItem.experiencias:
        return ExperiencesModuleScreen(
          catalogsModule: widget.catalogsModule,
          authController: widget.authController,
        );
      case AppNavItem.mas:
        return MoreFlowScreen(
          controller: widget.authController,
          contactsApiClient: widget.contactsApiClient,
          catalogsModule: widget.catalogsModule,
          saddlesModule: widget.saddlesModule,
          providersModule: widget.providersModule,
          onCallRequested: widget.onCallRequested,
        );
      case AppNavItem.none:
        return const SizedBox.shrink();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([widget.authController, _shellNav]),
      builder: (context, _) {
        final canReachBackend =
            widget.authController.networkStatus.canReachBackend;
        if (canReachBackend && !_wasBackendReachable) {
          if (widget.catalogsModule != null) {
            unawaited(widget.catalogsModule!.repository.autoSync());
          }
          // Vaciar la cola de salida compartida (asignaciones, saddles).
          unawaited(widget.outbox?.autoSync() ?? Future<void>.value());
        }
        _wasBackendReachable = canReachBackend;

        final showReconnectOverlay =
            widget.authController.isLoading &&
            widget.authController.authState ==
                LocalAuthState.signedInLocalUnverified &&
            widget.authController.networkStatus.linkType != LinkType.offline;

        return Stack(
          children: [
            Scaffold(
              appBar: const AppTopBar(
                logoAssetPath: 'assets/branding/lajuana-banner.svg',
              ),
              body: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ShellStatusRegion(controller: widget.authController),
                  Expanded(
                    child: RefreshScope(
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          for (final tab in _visitedTabs)
                            Offstage(
                              offstage: _shellNav.currentTab != tab,
                              child: TickerMode(
                                enabled: _shellNav.currentTab == tab,
                                child: Navigator(
                                  key: _navigatorKeys[tab],
                                    onGenerateRoute: (settings) {
                                      return MaterialPageRoute<void>(
                                        builder: (ctx) {
                                        // El scroll se maneja globalmente via RefreshScope.
                                        if (tab == AppNavItem.reservas || tab == AppNavItem.equinos || tab == AppNavItem.experiencias) {
                                          return _tabRoot(tab);
                                        }
                                          return SingleChildScrollView(
                                            physics: const AlwaysScrollableScrollPhysics(),
                                            child: _tabRoot(tab),
                                          );
                                        },
                                        settings: settings,
                                      );
                                    },
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              bottomNavigationBar: AppBottomNav(
                current: _shellNav.currentTab,
                onTap: _onBottomNavTap,
              ),
            ),
            if (showReconnectOverlay) ...[
              const Positioned.fill(
                child: ModalBarrier(dismissible: false, color: Colors.black54),
              ),
              const Positioned.fill(child: _ReconnectLoadingView()),
            ],
          ],
        );
      },
    );
  }
}

class _ReconnectLoadingView extends StatelessWidget {
  const _ReconnectLoadingView();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Container(
        width: 280,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        decoration: BoxDecoration(
          color: scheme.surfaceContainerHigh,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: scheme.outlineVariant),
        ),
        child: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2.4),
            ),
            SizedBox(height: 12),
            Text('Reconectando sesion...', textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
