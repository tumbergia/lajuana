import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservations_list_controller.dart';
import 'package:mobile/features/reservations/presentation/models/reservation_view_models.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/features/dashboard/presentation/controllers/dashboard_controller.dart';
import 'package:mobile/features/dashboard/presentation/widgets/dashboard_departures_block.dart';
import 'package:mobile/features/dashboard/presentation/widgets/dashboard_pending_block.dart';
import 'package:mobile/features/dashboard/presentation/widgets/dashboard_summary_block.dart';
import 'package:mobile/features/dashboard/presentation/widgets/dashboard_sync_block.dart';
import 'package:mobile/features/shared/presentation/widgets/module_subroute_header.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({
    super.key,
    required this.authController,
    required this.onNavigateToTab,
    this.reservationsModule,
    this.catalogsModule,
  });

  final AuthController authController;
  final ValueChanged<AppNavItem> onNavigateToTab;
  final ReservationsModule? reservationsModule;
  final CatalogsModule? catalogsModule;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with RefreshableState {
  late final DashboardController _controller;
  ReservationsListController? _listController;
  bool _ownsListController = false;

  List<ReservationRecord> get _reservations =>
      _listController?.allItems ?? const [];

  @override
  void initState() {
    super.initState();
    _controller = DashboardController();
    _initListController();
  }

  void _initListController() {
    final module = widget.reservationsModule;
    if (module != null) {
      _listController = module.listController;
      _ownsListController = false;
      _listController!.addListener(_onListChanged);
      if (_listController!.state == ReservationsLoadState.idle) {
        _listController!.loadInitial();
      }
    }
  }

  void _onListChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    super.dispose();
    _listController?.removeListener(_onListChanged);
    if (_ownsListController) {
      _listController?.dispose();
    }
    _controller.dispose();
  }

  @override
  Future<void> onRefresh() async {
    final futures = <Future<void>>[];
    if (_listController != null) {
      futures.add(_listController!.refresh());
    }
    final catalogs = widget.catalogsModule?.repository;
    if (catalogs != null) {
      futures.add(catalogs.autoSync());
    }
    if (_controller.subroute == DashboardSubroute.sync) {
      futures.add(widget.authController.refreshRequested());
    }
    await Future.wait(futures);
  }

  void _openReservationDetail(ReservationRecord reservation) {
    widget.onNavigateToTab(AppNavItem.reservas);
  }

  int _pendingCount(List<ReservationRecord> items) =>
      items.where((item) => item.status == 'pendientes').length;

  int _todayCount(List<ReservationRecord> items) {
    final today = DateTime.now();
    final todayPrefix =
        '${today.day.toString().padLeft(2, '0')} ${_monthShort(today.month)} ${today.year}';
    return items
        .where((item) => item.slotLabel.startsWith(todayPrefix))
        .length;
  }

  String _monthShort(int month) {
    const labels = [
      'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
    ];
    return labels[month - 1];
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_controller, if (_listController != null) _listController!]),
      builder: (context, _) {
        final reservations = _reservations;
        final pendingCount = _pendingCount(reservations);
        final todayCount = _todayCount(reservations);

        return RefreshableViewport(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ModuleSubrouteHeader(
                eyebrow: 'Inicio',
                title: 'Tablero operativo',
                subtitle: 'Operacion de reservas y estado del dia',
                subrouteLabels: const [
                  'Resumen',
                  'Pendientes',
                  'Salidas',
                  'Sync',
                ],
                currentSubrouteIndex: _controller.subroute.index,
                onSubrouteTap: _controller.selectSubrouteByIndex,
              ),
              const SizedBox(height: 20),
              _buildSubroute(
                pendingCount: pendingCount,
                todayCount: todayCount,
                reservations: reservations,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSubroute({
    required int pendingCount,
    required int todayCount,
    required List<ReservationRecord> reservations,
  }) {
    switch (_controller.subroute) {
      case DashboardSubroute.resumen:
        return DashboardSummaryBlock(
          pendingCount: pendingCount,
          todayCount: todayCount,
          onOpenReservations: () => widget.onNavigateToTab(AppNavItem.reservas),
          onOpenEquines: () => widget.onNavigateToTab(AppNavItem.equinos),
          onOpenExperiencias: () =>
              widget.onNavigateToTab(AppNavItem.experiencias),
        );
      case DashboardSubroute.pendientes:
        return DashboardPendingBlock(
          reservations: reservations,
          onOpenReservationDetail: _openReservationDetail,
        );
      case DashboardSubroute.salidas:
        return DashboardDeparturesBlock(reservations: reservations);
      case DashboardSubroute.sync:
        return DashboardSyncBlock(
          authController: widget.authController,
          reservations: reservations,
        );
    }
  }
}
