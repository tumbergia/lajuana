import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_api_client.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/widgets/session_loading_view.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/app/navigation/shell_navigation_controller.dart';
import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';
import 'package:mobile_ui/src/widgets/app_top_bar.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_ui/src/widgets/voice_pull_scope.dart';
import 'widgets/shell_status_region.dart';
import 'package:mobile/features/configuration/presentation/screens/more_flow_screen.dart';
import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/notifications/notifications_module.dart';
import 'package:mobile/features/notifications/presentation/screens/notifications_screen.dart';
import 'package:mobile/features/notifications/presentation/widgets/notification_heads_up.dart';
import 'package:mobile/features/notifications/infrastructure/notification_background_service.dart';
import 'package:mobile/features/dashboard/presentation/screens/dashboard_screen.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile/features/equines/presentation/screens/equines_module_screen.dart';
import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/reservations/presentation/screens/reservations_module_screen.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/features/saddles/saddles_module.dart';
import 'package:mobile/features/providers/providers_module.dart';
import 'package:mobile/features/voice_assistant/presentation/voice_sheet_launcher.dart';
import 'package:mobile/features/voice_assistant/presentation/navigation/voice_assistant_navigation.dart';
import 'package:mobile/features/voice_assistant/voice_assistant_module.dart';

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
    required this.voiceAssistantModule,
    this.configurationModule,
    this.notificationsModule,
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
  final VoiceAssistantModule voiceAssistantModule;
  final LaJuanaConfigurationModule? configurationModule;
  final NotificationsModule? notificationsModule;
  final Future<bool> Function(String phone)? onCallRequested;

  @override
  State<AuthenticatedShell> createState() => _AuthenticatedShellState();
}

class _AuthenticatedShellState extends State<AuthenticatedShell>
    with WidgetsBindingObserver {
  /// Intervalo del reintento periódico de sincronización en segundo plano.
  static const _periodicSyncInterval = Duration(seconds: 90);

  late final ShellNavigationController _shellNav;
  final Map<AppNavItem, GlobalKey<NavigatorState>> _navigatorKeys = {};
  final Set<AppNavItem> _visitedTabs = {};
  BackendReachability _lastReachability = BackendReachability.unknown;
  Timer? _syncTimer;
  bool _isSyncing = false;
  DateTime? _lastBackPress;

  @override
  void initState() {
    super.initState();
    _shellNav = ShellNavigationController();
    _ensureTab(AppNavItem.inicio);
    WidgetsBinding.instance.addObserver(this);
    // Carga el conteo de ítems que quedaron en cola de sesiones previas.
    unawaited(widget.outbox?.refreshCachedPendingCount() ?? Future<void>.value());
    // Vacía cualquier cola pendiente al arrancar y arranca el reintento
    // periódico para que la sincronización sea automática y transparente.
    // Solo si hay fuentes de sincronización (evita timers ociosos en tests).
    if (widget.catalogsModule != null ||
        widget.outbox != null ||
        widget.reservationsModule != null) {
      unawaited(_syncAll());
      _syncTimer = Timer.periodic(
        _periodicSyncInterval,
        (_) => unawaited(_maybeSync()),
      );
    }
    // Defer so notifyListeners does not mark the shell dirty during mount.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      widget.notificationsModule?.controller.startForegroundPolling();
      unawaited(_registerBackgroundNotifications());
    });
  }

  Future<void> _registerBackgroundNotifications() async {
    final module = widget.notificationsModule;
    if (module == null) return;
    final enabled = await NotificationBackgroundService.isEnabled();
    module.controller.setBackgroundPollingEnabled(enabled);
    if (enabled) {
      await NotificationBackgroundService.requestPermissions();
      await NotificationBackgroundService.registerPeriodic();
    }
  }

  void _openNotificationsInbox({String? openNotificationId}) {
    final module = widget.notificationsModule;
    if (module == null) return;
    module.controller.dismissArrivalBanner();
    final nav = _navigatorKeys[_shellNav.currentTab]?.currentState;
    nav?.push(
      MaterialPageRoute<void>(
        builder: (_) => NotificationsScreen(
          controller: module.controller,
          reservationsModule: widget.reservationsModule,
          catalogsModule: widget.catalogsModule,
          authController: widget.authController,
          assignmentsModule: widget.assignmentsModule,
          initialOpenNotificationId: openNotificationId,
        ),
      ),
    );
  }

  @override
  void dispose() {
    _syncTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    widget.notificationsModule?.controller.stopForegroundPolling();
    _shellNav.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Al volver a primer plano intentamos vaciar la cola de inmediato.
    if (state == AppLifecycleState.resumed) {
      unawaited(_maybeSync());
    }
  }

  /// Re-verifica conectividad real y sincroniza si corresponde; usado por el
  /// timer periódico y el ciclo de vida (resume). La re-verificación es la
  /// única forma de detectar que el backend cayó mientras el enlace de red
  /// sigue activo (ver `AuthController.recheckNetworkStatus`).
  Future<void> _maybeSync() async {
    await widget.authController.recheckNetworkStatus();
    if (widget.authController.networkStatus.canReachBackend) {
      unawaited(_syncAll());
    }
  }

  /// Vacía todas las colas de salida (catálogos + outbox compartido),
  /// reintentando también las operaciones que habían fallado. Best-effort:
  /// nunca lanza, para poder invocarse desde timers/lifecycle sin riesgo.
  Future<void> _syncAll() async {
    if (_isSyncing) return;
    _isSyncing = true;
    try {
      final catalogs = widget.catalogsModule?.repository;
      if (catalogs != null) {
        try {
          await catalogs.syncNow(includeFailed: true);
        } catch (_) {
          // Ignorado: la sincronización se reintenta sola en el próximo ciclo.
        }
      }
      try {
        await (widget.outbox?.autoSync() ?? Future<void>.value());
      } catch (_) {
        // Ignorado: idem.
      }
      final reservations = widget.reservationsModule?.repository;
      if (reservations != null) {
        try {
          await reservations.syncNow();
        } catch (_) {
          // Ignorado: idem — reservas/participantes/comprobantes se
          // reintentan solos en el próximo ciclo.
        }
      }
    } finally {
      _isSyncing = false;
    }
  }

  void _ensureTab(AppNavItem tab) {
    if (tab == AppNavItem.none) return;
    _visitedTabs.add(tab);
    _navigatorKeys.putIfAbsent(tab, () => GlobalKey<NavigatorState>());
  }

  void _onBottomNavTap(AppNavItem item) {
    if (item == AppNavItem.none) return;
    // Experiencias ya no es tab independiente — redirige a Más.
    if (item == AppNavItem.experiencias) {
      item = AppNavItem.mas;
    }
    _ensureTab(item);
    _shellNav.selectTab(item);
    setState(() {});
  }

  bool get _isAdminVoiceEnabled {
    final user = widget.authController.currentUser;
    return widget.authController.authState == LocalAuthState.signedInVerified &&
        user?.role == 'admin';
  }

  Future<void> _openAdminVoiceSheet() async {
    if (!_isAdminVoiceEnabled) return;
    await openAdminVoiceSheet(
      context,
      controller: widget.voiceAssistantModule.controller,
      navigation: VoiceAssistantNavigation(
        authController: widget.authController,
        equineRepository: widget.equineRepository,
        equineEventRepository: widget.equineEventRepository,
        reservationsModule: widget.reservationsModule,
        catalogsModule: widget.catalogsModule,
        saddlesModule: widget.saddlesModule,
        providersModule: widget.providersModule,
        assignmentsModule: widget.assignmentsModule,
      ),
    );
  }

  Widget _tabRoot(AppNavItem tab) {
    switch (tab) {
      case AppNavItem.inicio:
        return DashboardScreen(
          authController: widget.authController,
          onNavigateToTab: _onBottomNavTap,
          reservationsModule: widget.reservationsModule,
          catalogsModule: widget.catalogsModule,
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
      case AppNavItem.mas:
        return MoreFlowScreen(
          controller: widget.authController,
          contactsApiClient: widget.contactsApiClient,
          catalogsModule: widget.catalogsModule,
          saddlesModule: widget.saddlesModule,
          providersModule: widget.providersModule,
          onCallRequested: widget.onCallRequested,
          configurationModule: widget.configurationModule,
          reservationsModule: widget.reservationsModule,
          notificationsModule: widget.notificationsModule,
        );
      case AppNavItem.experiencias:
        // Experiencias ahora vive dentro de Más — no debería llegar aquí.
        // Se deja como redirect defensivo.
        return MoreFlowScreen(
          controller: widget.authController,
          contactsApiClient: widget.contactsApiClient,
          catalogsModule: widget.catalogsModule,
          saddlesModule: widget.saddlesModule,
          providersModule: widget.providersModule,
          onCallRequested: widget.onCallRequested,
          configurationModule: widget.configurationModule,
          reservationsModule: widget.reservationsModule,
          notificationsModule: widget.notificationsModule,
        );
      case AppNavItem.none:
        return const SizedBox.shrink();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([
        widget.authController,
        _shellNav,
        if (widget.notificationsModule != null)
          widget.notificationsModule!.controller,
      ]),
      builder: (context, _) {
        final reachability =
            widget.authController.networkStatus.backendReachability;
        if (reachability == BackendReachability.reachable &&
            _lastReachability != BackendReachability.reachable) {
          // Recuperamos el backend: vaciamos las colas (incluye fallidas).
          unawaited(_syncAll());
          // Defer unread refresh: calling notifyListeners mid-build crashes
          // the AnimatedBuilder that listens to NotificationsController.
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!mounted) return;
            unawaited(
              widget.notificationsModule?.controller.refreshUnreadCount() ??
                  Future<void>.value(),
            );
          });
        } else if (reachability == BackendReachability.unreachable &&
            _lastReachability == BackendReachability.reachable) {
          // Se perdió el backend: aviso efímero como toast superior en vez de
          // un banner persistente.
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!mounted) return;
            showAppTopToast(
              context,
              message:
                  'Servidor no alcanzable. Revisa tu conexión o que el API esté en marcha.',
              isError: true,
              icon: Icons.cloud_off_rounded,
            );
          });
        }
        _lastReachability = reachability;

        final showReconnectOverlay =
            widget.authController.isLoading &&
            widget.authController.authState ==
                LocalAuthState.signedInLocalUnverified &&
            widget.authController.networkStatus.linkType != LinkType.offline;

        final unread = widget.notificationsModule?.controller.unreadCount ?? 0;
        final notificationsController = widget.notificationsModule?.controller;
        final showHeadsUp = notificationsController?.hasArrivalBanner == true;

        return PopScope(
          canPop: false,
          onPopInvokedWithResult: (didPop, _) {
            if (didPop) return;
            // 1. Si el tab activo tiene una sub-ruta abierta (detalle, formulario),
            //    el back la cierra primero.
            final activeNav =
                _navigatorKeys[_shellNav.currentTab]?.currentState;
            if (activeNav != null && activeNav.canPop()) {
              activeNav.pop();
              return;
            }
            // 2. Si no hay sub-ruta, regresa al tab visitado anteriormente.
            if (_shellNav.goBack()) {
              _ensureTab(_shellNav.currentTab);
              setState(() {});
              return;
            }
            // 3. Sin historial de tabs: doble-tap para salir de la app.
            final now = DateTime.now();
            if (_lastBackPress != null &&
                now.difference(_lastBackPress!) <
                    const Duration(seconds: 2)) {
              SystemNavigator.pop();
              return;
            }
            _lastBackPress = now;
            ScaffoldMessenger.of(context)
              ..hideCurrentSnackBar()
              ..showSnackBar(
                const SnackBar(
                  content: Text('Presiona atrás otra vez para salir'),
                  duration: Duration(seconds: 2),
                ),
              );
          },
          child: Stack(
          children: [
            Scaffold(
              appBar: AppTopBar(
                logoAssetPath: 'assets/branding/lajuana-banner.svg',
                // Un solo ícono para "no hay conexión completa con el
                // servidor": sin enlace de red O sesión sin poder verificarse
                // (isOfflineRestricted, que en la práctica siempre implica que
                // el backend no respondió). Antes eran dos indicadores
                // separados (ícono + banner "Sesión local") — se unifican
                // para no confundir al usuario con dos avisos distintos.
                showOfflineIndicator:
                    widget.authController.networkStatus.linkType ==
                        LinkType.offline ||
                    widget.authController.isOfflineRestricted,
                onOfflineTap: () => showAppTopToast(
                  context,
                  message: widget.authController.networkStatus.linkType ==
                          LinkType.offline
                      ? 'Sin Wi‑Fi ni datos. El modo local sigue disponible si aplica.'
                      : 'Sin conexión con el servidor. Sesión local: acciones críticas están bloqueadas.',
                  icon: Icons.wifi_off_rounded,
                ),
                showNotificationDot: unread > 0,
                onNotificationsTap: widget.notificationsModule == null
                    ? null
                    : () => _openNotificationsInbox(),
              ),
              body: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ShellStatusRegion(
                    controller: widget.authController,
                  ),
                  Expanded(
                    child: VoicePullScope(
                      enabled: _isAdminVoiceEnabled,
                      displacement: MediaQuery.of(context).padding.bottom + 72,
                      onTriggered: _openAdminVoiceSheet,
                      child: RefreshScope(
                        onAfterRefresh: _maybeSync,
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
                                        builder: (ctx) => _tabRoot(tab),
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
                  ),
                ],
              ),
              bottomNavigationBar: AppBottomNav(
                current: _shellNav.currentTab,
                onTap: _onBottomNavTap,
                onVoiceLongPress: _isAdminVoiceEnabled
                    ? (_, _) => _openAdminVoiceSheet()
                    : null,
              ),
            ),
            if (showHeadsUp && notificationsController != null)
              NotificationHeadsUp(
                key: ValueKey(
                  'arrival-${notificationsController.pendingArrivalId}-'
                  '${notificationsController.pendingArrivalCount}',
                ),
                title: notificationsController.pendingArrivalTitle!,
                body: notificationsController.pendingArrivalBody,
                eventType: notificationsController.pendingArrivalEventType,
                count: notificationsController.pendingArrivalCount,
                onTap: () => _openNotificationsInbox(
                  openNotificationId:
                      notificationsController.pendingArrivalId,
                ),
                onDismiss: notificationsController.dismissArrivalBanner,
              ),
            if (showReconnectOverlay)
              const Positioned.fill(child: SessionLoadingView()),
          ],
          ),
        );
      },
    );
  }
}
