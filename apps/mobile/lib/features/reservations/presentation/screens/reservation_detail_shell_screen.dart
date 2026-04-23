import 'package:flutter/material.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_segmented_filter.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_scaffold.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_status_banner.dart';
import '../../../../app/widgets/app_timeline.dart';
import '../models/reservation_view_models.dart';

enum ReservationDetailSubroute {
  resumen,
  participantes,
  pagos,
  asignaciones,
  bitacora,
}

/// Detalle de reserva dentro del shell: sin segunda [AppTopBar]; cabecera de módulo + secciones.
class ReservationDetailShellScreen extends StatefulWidget {
  const ReservationDetailShellScreen({
    super.key,
    required this.reservation,
    required this.participants,
    required this.paymentProofs,
    required this.assignments,
  });

  final ReservationRecord reservation;
  final List<ReservationParticipantRecord> participants;
  final List<ReservationPaymentProofRecord> paymentProofs;
  final List<ReservationAssignmentRecord> assignments;

  @override
  State<ReservationDetailShellScreen> createState() =>
      _ReservationDetailShellScreenState();
}

class _ReservationDetailShellScreenState
    extends State<ReservationDetailShellScreen> {
  ReservationDetailSubroute _subroute = ReservationDetailSubroute.resumen;

  @override
  Widget build(BuildContext context) {
    final reservation = widget.reservation;

    return AppScaffold(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Reservas',
            title: 'Detalle ${reservation.code}',
            subtitle: '${reservation.clientName} - ${reservation.equineName}',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.of(context).maybePop(),
            ),
          ),
          const SizedBox(height: 12),
          AppSegmentedFilter<int>(
            value: _subroute.index,
            onChanged: (index) {
              setState(() {
                _subroute = ReservationDetailSubroute.values[index];
              });
            },
            items: const [
              AppSegmentedFilterItem(label: 'Resumen', value: 0),
              AppSegmentedFilterItem(label: 'Participantes', value: 1),
              AppSegmentedFilterItem(label: 'Pagos', value: 2),
              AppSegmentedFilterItem(label: 'Asignaciones', value: 3),
              AppSegmentedFilterItem(label: 'Bitacora', value: 4),
            ],
          ),
          const SizedBox(height: 12),
          ..._buildStatusBanners(reservation),
          if (_hasStatusBanners(reservation)) const SizedBox(height: 12),
          _buildSubrouteContent(reservation),
        ],
      ),
    );
  }

  bool _hasStatusBanners(ReservationRecord reservation) {
    return reservation.hasPendingSync || reservation.hasSyncError;
  }

  List<Widget> _buildStatusBanners(ReservationRecord reservation) {
    final banners = <Widget>[];
    if (reservation.hasPendingSync) {
      banners.add(
        const AppStatusBanner(
          title: 'Cambios pendientes',
          message: 'Esta reserva tiene cambios locales en espera de sync.',
          tone: AppStatusBannerTone.warning,
          icon: Icons.sync_problem_rounded,
          badgeLabel: 'Pendiente',
        ),
      );
    }

    if (reservation.hasSyncError) {
      banners.add(
        const AppStatusBanner(
          title: 'Error de sincronizacion',
          message: 'Ultimo intento remoto fallo. Reintenta cuando haya red.',
          tone: AppStatusBannerTone.danger,
          icon: Icons.warning_amber_rounded,
          badgeLabel: 'Error',
        ),
      );
    }

    return banners;
  }

  Widget _buildSubrouteContent(ReservationRecord reservation) {
    switch (_subroute) {
      case ReservationDetailSubroute.resumen:
        return _buildSummary(reservation);
      case ReservationDetailSubroute.participantes:
        return _buildParticipants(reservation);
      case ReservationDetailSubroute.pagos:
        return _buildPaymentProofs(reservation);
      case ReservationDetailSubroute.asignaciones:
        return _buildAssignments(reservation);
      case ReservationDetailSubroute.bitacora:
        return _buildTimeline(reservation);
    }
  }

  Widget _buildSummary(ReservationRecord reservation) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppEntityRowCard(
          title: reservation.clientName,
          subtitle: 'Cliente principal',
          badge: _statusBadgeForReservation(reservation),
          selected: true,
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: reservation.equineName,
          subtitle: 'Equino asignado',
          leading: const Icon(Icons.hail_rounded, size: 18),
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: reservation.slotLabel,
          subtitle: 'Horario operativo',
          leading: const Icon(Icons.schedule_rounded, size: 18),
        ),
      ],
    );
  }

  Widget _buildParticipants(ReservationRecord reservation) {
    final items = widget.participants
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);
    if (items.isEmpty) {
      return const AppEntityRowCard(
        title: 'Sin participantes',
        subtitle: 'No hay registros para esta reserva',
        selected: true,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (int i = 0; i < items.length; i++) ...[
          AppEntityRowCard(
            title: items[i].fullName,
            subtitle: 'Completitud ${items[i].completionLabel}',
            badge: AppBadge(
              label: items[i].isComplete ? 'Completo' : 'Incompleto',
              tone: items[i].isComplete
                  ? AppBadgeTone.success
                  : AppBadgeTone.warning,
              uppercase: false,
            ),
          ),
          if (i != items.length - 1) const SizedBox(height: 10),
        ],
      ],
    );
  }

  Widget _buildPaymentProofs(ReservationRecord reservation) {
    final items = widget.paymentProofs
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);
    if (items.isEmpty) {
      return const AppEntityRowCard(
        title: 'Sin comprobantes',
        subtitle: 'No hay comprobantes registrados para esta reserva',
        selected: true,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (int i = 0; i < items.length; i++) ...[
          AppEntityRowCard(
            title: items[i].proofCode,
            subtitle: 'Comprobante de pago',
            leading: const Icon(Icons.receipt_long_rounded, size: 18),
            badge: AppBadge(
              label: items[i].statusLabel,
              tone: items[i].statusTone,
              uppercase: false,
            ),
          ),
          if (i != items.length - 1) const SizedBox(height: 10),
        ],
      ],
    );
  }

  Widget _buildAssignments(ReservationRecord reservation) {
    final items = widget.assignments
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);
    if (items.isEmpty) {
      return const AppEntityRowCard(
        title: 'Sin asignaciones',
        subtitle: 'No hay asignaciones para esta reserva',
        selected: true,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (int i = 0; i < items.length; i++) ...[
          AppEntityRowCard(
            title: items[i].equine,
            subtitle: 'Responsable ${items[i].rider}',
            leading: const Icon(Icons.shield_moon_outlined, size: 18),
            badge: AppBadge(
              label: items[i].statusLabel,
              tone: items[i].statusTone,
              uppercase: false,
            ),
          ),
          if (i != items.length - 1) const SizedBox(height: 10),
        ],
      ],
    );
  }

  Widget _buildTimeline(ReservationRecord reservation) {
    return AppTimeline(
      children: [
        AppTimelineItem(
          state: AppTimelineNodeState.active,
          child: AppTimelineEntryCard(
            date: '${reservation.slotLabel} - 10:05',
            title: 'Ajuste operativo',
            badge: const AppBadge(
              label: 'Pendiente',
              tone: AppBadgeTone.warning,
            ),
            description:
                'Se valido disponibilidad para ${reservation.equineName}.',
          ),
        ),
        AppTimelineItem(
          state: AppTimelineNodeState.completed,
          child: AppTimelineEntryCard(
            date: '${reservation.slotLabel} - 09:15',
            title: 'Participante verificado',
            badge: const AppBadge(label: 'OK', tone: AppBadgeTone.success),
            description: 'Validacion documental completada para esta reserva.',
          ),
        ),
      ],
    );
  }

  AppBadge _statusBadgeForReservation(ReservationRecord reservation) {
    switch (reservation.status) {
      case 'pendientes':
        return const AppBadge(
          label: 'Pendiente',
          tone: AppBadgeTone.warning,
          uppercase: false,
        );
      case 'confirmadas':
        return const AppBadge(
          label: 'Confirmada',
          tone: AppBadgeTone.primary,
          uppercase: false,
        );
      case 'finalizadas':
        return const AppBadge(
          label: 'Finalizada',
          tone: AppBadgeTone.success,
          uppercase: false,
        );
      default:
        return const AppBadge(
          label: 'Sin estado',
          tone: AppBadgeTone.neutral,
          uppercase: false,
        );
    }
  }
}

typedef ReservationDetailScreen = ReservationDetailShellScreen;
