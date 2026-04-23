import 'package:flutter/material.dart';

import '../../../../app/widgets/app_entity_row_card.dart';
import '../../../../app/widgets/app_metric_card.dart';
class DashboardSummaryBlock extends StatelessWidget {
  const DashboardSummaryBlock({
    super.key,
    required this.pendingCount,
    required this.todayCount,
    required this.onOpenReservations,
    required this.onOpenEquines,
    required this.onOpenParticipants,
  });

  final int pendingCount;
  final int todayCount;
  final VoidCallback onOpenReservations;
  final VoidCallback onOpenEquines;
  final VoidCallback onOpenParticipants;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppMetricCard(
          title: 'Reservas pendientes',
          value: pendingCount.toString().padLeft(2, '0'),
          suffix: 'CASOS',
          supportingText: 'Requieren accion operativa',
        ),
        const SizedBox(height: 12),
        AppMetricCard(
          title: 'Salidas proximas',
          value: todayCount.toString().padLeft(2, '0'),
          suffix: 'HOY',
          tone: AppMetricCardTone.inverse,
        ),
        const SizedBox(height: 16),
        AppEntityRowCard(
          title: 'Abrir reservas',
          subtitle: 'Gestion de detalle, participantes y pagos',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: onOpenReservations,
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: 'Abrir equinos',
          subtitle: 'Disponibilidad y asignaciones en campo',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: onOpenEquines,
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: 'Abrir participantes',
          subtitle: 'Completitud y validaciones por reserva',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: onOpenParticipants,
        ),
      ],
    );
  }
}
