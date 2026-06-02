import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/reservations/presentation/models/reservation_view_models.dart';
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
  });

  final AuthController authController;
  final ValueChanged<AppNavItem> onNavigateToTab;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  static const List<ReservationRecord> _reservations =
      ReservationPresentationFixtures.reservations;
  static const List<ReservationParticipantRecord> _participants =
      ReservationPresentationFixtures.participants;
  static const List<ReservationPaymentProofRecord> _paymentProofs =
      ReservationPresentationFixtures.paymentProofs;
  static const List<ReservationAssignmentRecord> _assignments =
      ReservationPresentationFixtures.assignments;

  late final DashboardController _controller;

  @override
  void initState() {
    super.initState();
    _controller = DashboardController();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _openReservationDetail(ReservationRecord reservation) {
    // Phase 1: redirect to Reservations tab. Detail with real data coming in next phase.
    widget.onNavigateToTab(AppNavItem.reservas);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final pendingCount = _reservations
            .where((item) => item.status == 'pendientes')
            .length;
        final todayCount = _reservations.where((item) {
          return item.slotLabel.startsWith('24 Oct 2026');
        }).length;

        return Padding(
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
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSubroute({required int pendingCount, required int todayCount}) {
    switch (_controller.subroute) {
      case DashboardSubroute.resumen:
        return DashboardSummaryBlock(
          pendingCount: pendingCount,
          todayCount: todayCount,
          onOpenReservations: () => widget.onNavigateToTab(AppNavItem.reservas),
          onOpenEquines: () => widget.onNavigateToTab(AppNavItem.equinos),
          onOpenParticipants: () => widget.onNavigateToTab(AppNavItem.clientes),
        );
      case DashboardSubroute.pendientes:
        return DashboardPendingBlock(
          reservations: _reservations,
          onOpenReservationDetail: _openReservationDetail,
        );
      case DashboardSubroute.salidas:
        return DashboardDeparturesBlock(reservations: _reservations);
      case DashboardSubroute.sync:
        return DashboardSyncBlock(
          authController: widget.authController,
          reservations: _reservations,
        );
    }
  }
}
