import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/domain/analytics_models.dart';
import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/equines/presentation/screens/equines_module_screen.dart';
import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile/features/reservations/presentation/models/reservation_view_models.dart';
import 'package:mobile/features/reservations/presentation/screens/reservation_detail_shell_screen.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_row_card.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';

/// Lista drill-down de un ítem de Tareas pendientes, reutilizando row cards.
class ActionPendingListScreen extends StatefulWidget {
  const ActionPendingListScreen({
    super.key,
    required this.item,
    this.reservationsModule,
    this.authController,
    this.catalogsModule,
    this.assignmentsModule,
    this.equineRepository,
    this.equineEventRepository,
    this.userRole,
  });

  final BreakdownItem item;
  final ReservationsModule? reservationsModule;
  final AuthController? authController;
  final CatalogsModule? catalogsModule;
  final AssignmentsModule? assignmentsModule;
  final EquineRepository? equineRepository;
  final EquineEventRepository? equineEventRepository;
  final String? userRole;

  static bool isEquineCare(String key) => key == 'overdue_care';

  static bool isReservationBucket(String key) =>
      key == 'contact' ||
      key == 'pending_payment' ||
      key == 'payment_received' ||
      key == 'pay_received';

  @override
  State<ActionPendingListScreen> createState() =>
      _ActionPendingListScreenState();
}

class _ActionPendingListScreenState extends State<ActionPendingListScreen> {
  bool _loading = true;
  String? _error;
  List<ReservationRecord> _reservations = const [];

  @override
  void initState() {
    super.initState();
    if (ActionPendingListScreen.isReservationBucket(widget.item.key)) {
      _loadReservations();
    } else {
      _loading = false;
    }
  }

  Future<void> _loadReservations() async {
    final module = widget.reservationsModule;
    if (module == null) {
      setState(() {
        _loading = false;
        _error = 'No hay módulo de reservas disponible.';
      });
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      var source = module.listController.allItems;
      if (source.isEmpty) {
        await module.listController.loadInitial();
        source = module.listController.allItems;
      }
      final filtered = source
          .where((r) => !r.isDeleted && _matchesReservation(r, widget.item.key))
          .toList(growable: false);
      if (!mounted) return;
      setState(() {
        _reservations = filtered;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'No se pudo cargar el listado.';
      });
    }
  }

  static bool _matchesReservation(ReservationRecord r, String key) {
    final raw = r.statusRaw;
    ReservationStatus? status;
    if (raw is ReservationStatus) {
      status = raw;
    } else if (raw != null) {
      status = parseReservationStatus(raw.toString());
    }
    if (status == null) return false;
    switch (key) {
      case 'contact':
        return status == ReservationStatus.contact;
      case 'pending_payment':
        return status == ReservationStatus.pendingPayment;
      case 'payment_received':
      case 'pay_received':
        return status == ReservationStatus.paymentReceived ||
            (r.paymentStatus?.toLowerCase() == 'received');
      default:
        return false;
    }
  }

  void _openReservation(ReservationRecord reservation) {
    final id = reservation.id;
    if (id == null || id.isEmpty) return;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ReservationDetailShellScreen(
          reservationId: id,
          reservationsModule: widget.reservationsModule,
          catalogsModule: widget.catalogsModule,
          authController: widget.authController,
          assignmentsModule: widget.assignmentsModule,
        ),
      ),
    );
  }

  Widget _listAppBarTitle(BuildContext context) {
    final base = Theme.of(context).appBarTheme.titleTextStyle;
    return Text(
      widget.item.label.toUpperCase(),
      style: base?.copyWith(letterSpacing: 0),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (ActionPendingListScreen.isEquineCare(widget.item.key) &&
        widget.equineRepository != null &&
        widget.equineEventRepository != null) {
      return Scaffold(
        appBar: AppBar(title: _listAppBarTitle(context)),
        body: EquinesModuleScreen(
          repository: widget.equineRepository!,
          eventRepository: widget.equineEventRepository!,
          userRole: widget.userRole,
        ),
      );
    }

    final tokens = Theme.of(context).appTokens;
    return Scaffold(
      appBar: AppBar(title: _listAppBarTitle(context)),
      body: _loading
          ? const AppCenteredLoader()
          : _error != null
              ? Center(
                  child: Padding(
                    padding: EdgeInsets.all(tokens.spaceLg),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_error!, textAlign: TextAlign.center),
                        SizedBox(height: tokens.spaceMd),
                        AppButton(
                          label: 'Reintentar',
                          onPressed: _loadReservations,
                          variant: AppButtonVariant.secondary,
                        ),
                      ],
                    ),
                  ),
                )
              : _reservations.isEmpty
                  ? const Center(
                      child: Text('No hay elementos en este momento.'),
                    )
                  : ListView.separated(
                      padding: EdgeInsets.all(tokens.spaceLg),
                      itemCount: _reservations.length,
                      separatorBuilder: (_, _) =>
                          SizedBox(height: tokens.spaceSm),
                      itemBuilder: (context, i) {
                        final r = _reservations[i];
                        return ReservationRowCard(
                          reservation: r,
                          subtitle: r.experienceName ?? r.equineName,
                          highlightIfPending: true,
                          openDetailsOnTap: true,
                          showRequestedDate: true,
                          onOpenDetail: () => _openReservation(r),
                        );
                      },
                    ),
    );
  }
}
