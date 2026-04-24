import 'package:flutter/material.dart';

import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_segmented_filter.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_timeline.dart';
import '../../../../app/widgets/app_badge.dart';
import '../../../auth/presentation/auth_controller.dart';
import '../../../catalogs/catalogs_module.dart';
import '../../../catalogs/schedules/presentation/pages/schedules_page.dart';
import '../controllers/reservations_controller.dart';
import '../controllers/reservations_list_controller.dart';
import '../models/reservation_view_models.dart';
import '../widgets/reservation_row_card.dart';
import 'reservation_detail_shell_screen.dart';
import '../../../shared/presentation/widgets/module_subroute_header.dart';

class ReservationsModuleScreen extends StatefulWidget {
  const ReservationsModuleScreen({
    super.key,
    this.catalogsModule,
    this.authController,
  });

  final CatalogsModule? catalogsModule;
  final AuthController? authController;

  @override
  State<ReservationsModuleScreen> createState() =>
      _ReservationsModuleScreenState();
}

class _ReservationsModuleScreenState extends State<ReservationsModuleScreen> {
  static const List<ReservationRecord> _reservations =
      ReservationPresentationFixtures.reservations;
  static const List<ReservationParticipantRecord> _participants =
      ReservationPresentationFixtures.participants;
  static const List<ReservationPaymentProofRecord> _paymentProofs =
      ReservationPresentationFixtures.paymentProofs;
  static const List<ReservationAssignmentRecord> _assignments =
      ReservationPresentationFixtures.assignments;

  late final ReservationsController _subrouteController;
  late final ReservationsListController _listController;

  @override
  void initState() {
    super.initState();
    _subrouteController = ReservationsController();
    _listController = ReservationsListController();
  }

  @override
  void dispose() {
    _subrouteController.dispose();
    _listController.dispose();
    super.dispose();
  }

  void _openReservationDetail(ReservationRecord reservation) {
    final participants = _participants
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);
    final paymentProofs = _paymentProofs
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);
    final assignments = _assignments
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);

    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) => ReservationDetailShellScreen(
          reservation: reservation,
          participants: participants,
          paymentProofs: paymentProofs,
          assignments: assignments,
        ),
      ),
    );
  }

  List<ReservationRecord> _filterReservations() {
    return _reservations
        .where((item) => item.status == _listController.filterValue)
        .toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_subrouteController, _listController]),
      builder: (context, _) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ModuleSubrouteHeader(
                eyebrow: 'Reservas',
                title: 'Operacion de reservas',
                subtitle: 'Local primero, sync visible y acciones por estado',
                subrouteLabels: const [
                  'Resumen',
                  'Participantes',
                  'Pagos',
                  'Asignaciones',
                  'Bitacora',
                ],
                currentSubrouteIndex: _subrouteController.subroute.index,
                onSubrouteTap: _subrouteController.selectSubrouteByIndex,
                trailing: AppButton(
                  label: widget.catalogsModule == null ? 'Crear' : 'Fechas',
                  icon: widget.catalogsModule == null
                      ? Icons.add
                      : Icons.calendar_today_rounded,
                  onPressed: widget.catalogsModule == null
                      ? () {}
                      : () {
                          if (widget.catalogsModule == null ||
                              widget.authController == null) {
                            return;
                          }
                          Navigator.of(context).push(
                            MaterialPageRoute<void>(
                              builder: (_) => SchedulesPage(
                                module: widget.catalogsModule!,
                                authController: widget.authController!,
                              ),
                            ),
                          );
                        },
                ),
              ),
              const SizedBox(height: 20),
              _buildSubrouteContent(),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSubrouteContent() {
    switch (_subrouteController.subroute) {
      case ReservationsSubroute.resumen:
        final filtered = _filterReservations();
        final visibleCount = _listController.visibleReservationCount;
        final visible = filtered.take(visibleCount).toList(growable: false);
        final canLoadMore = visible.length < filtered.length;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppSegmentedFilter<String>(
              value: _listController.filterValue,
              onChanged: _listController.setFilterValue,
              items: const [
                AppSegmentedFilterItem(
                  label: 'Pendientes',
                  value: 'pendientes',
                ),
                AppSegmentedFilterItem(
                  label: 'Confirmadas',
                  value: 'confirmadas',
                ),
                AppSegmentedFilterItem(
                  label: 'Finalizadas',
                  value: 'finalizadas',
                ),
              ],
            ),
            const SizedBox(height: 14),
            if (visible.isEmpty)
              const AppEntityRowCard(
                title: 'Sin resultados',
                subtitle: 'No hay reservas para el filtro seleccionado',
                selected: true,
              )
            else
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: visible.length,
                itemBuilder: (context, i) {
                  return Padding(
                    padding: EdgeInsets.only(
                      bottom: i < visible.length - 1 ? 10 : 0,
                    ),
                    child: ReservationRowCard(
                      reservation: visible[i],
                      subtitle:
                          '${visible[i].equineName} - ${visible[i].slotLabel}',
                      highlightIfPending: true,
                      openDetailsOnTap: true,
                      onOpenDetail: () => _openReservationDetail(visible[i]),
                    ),
                  );
                },
              ),
            if (canLoadMore) ...[
              const SizedBox(height: 12),
              AppButton(
                label: 'Cargar mas',
                variant: AppButtonVariant.ghost,
                expanded: true,
                onPressed: () => _listController.loadMore(),
              ),
            ],
          ],
        );
      case ReservationsSubroute.participantes:
        return ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: _participants.length,
          itemBuilder: (context, i) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: i < _participants.length - 1 ? 10 : 0,
              ),
              child: AppEntityRowCard(
                title: _participants[i].fullName,
                subtitle: 'Reserva ${_participants[i].reservationCode}',
                badge: AppBadge(
                  label: _participants[i].completionLabel,
                  tone: _participants[i].isComplete
                      ? AppBadgeTone.success
                      : AppBadgeTone.warning,
                  uppercase: false,
                ),
                leading: const Icon(Icons.person_outline_rounded, size: 18),
              ),
            );
          },
        );
      case ReservationsSubroute.pagos:
        return ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: _paymentProofs.length,
          itemBuilder: (context, i) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: i < _paymentProofs.length - 1 ? 10 : 0,
              ),
              child: AppEntityRowCard(
                title: _paymentProofs[i].proofCode,
                subtitle: 'Reserva ${_paymentProofs[i].reservationCode}',
                badge: AppBadge(
                  label: _paymentProofs[i].statusLabel,
                  tone: _paymentProofs[i].statusTone,
                  uppercase: false,
                ),
                leading: const Icon(Icons.receipt_long_rounded, size: 18),
              ),
            );
          },
        );
      case ReservationsSubroute.asignaciones:
        return ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: _assignments.length,
          itemBuilder: (context, i) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: i < _assignments.length - 1 ? 10 : 0,
              ),
              child: AppEntityRowCard(
                title: _assignments[i].equine,
                subtitle:
                    'Reserva ${_assignments[i].reservationCode} - ${_assignments[i].rider}',
                badge: AppBadge(
                  label: _assignments[i].statusLabel,
                  tone: _assignments[i].statusTone,
                  uppercase: false,
                ),
                leading: const Icon(Icons.shield_moon_outlined, size: 18),
              ),
            );
          },
        );
      case ReservationsSubroute.bitacora:
        return const AppTimeline(
          children: [
            AppTimelineItem(
              state: AppTimelineNodeState.active,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 10:05',
                title: 'Cambio de horario',
                badge: AppBadge(label: 'Pendiente', tone: AppBadgeTone.warning),
                description: 'Se ajusto salida por condicion de pista.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.completed,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 09:15',
                title: 'Participante validado',
                badge: AppBadge(label: 'OK', tone: AppBadgeTone.success),
                description: 'Documento y consentimiento verificados.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.error,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 08:58',
                title: 'Fallo en carga de comprobante',
                badge: AppBadge(label: 'Error', tone: AppBadgeTone.danger),
                description: 'Se guardo localmente para reintento de sync.',
              ),
            ),
          ],
        );
    }
  }
}
