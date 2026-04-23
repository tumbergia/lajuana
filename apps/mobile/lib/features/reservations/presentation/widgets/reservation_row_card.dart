import 'package:flutter/material.dart';

import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_entity_row_card.dart';
import '../models/reservation_view_models.dart';

class ReservationRowCard extends StatelessWidget {
  const ReservationRowCard({
    super.key,
    required this.reservation,
    required this.subtitle,
    required this.highlightIfPending,
    required this.openDetailsOnTap,
    this.onOpenDetail,
  });

  final ReservationRecord reservation;
  final String subtitle;
  final bool highlightIfPending;
  final bool openDetailsOnTap;
  final VoidCallback? onOpenDetail;

  @override
  Widget build(BuildContext context) {
    final syncBadge = reservation.hasSyncError
        ? const AppBadge(
            label: 'Sync error',
            tone: AppBadgeTone.danger,
            uppercase: false,
          )
        : reservation.hasPendingSync
        ? const AppBadge(
            label: 'Pendiente',
            tone: AppBadgeTone.warning,
            uppercase: false,
          )
        : const AppBadge(
            label: 'OK',
            tone: AppBadgeTone.success,
            uppercase: false,
          );

    return AppEntityRowCard(
      title: reservation.clientName,
      subtitle: '$subtitle - ${reservation.code}',
      selected: highlightIfPending && reservation.status == 'pendientes',
      badge: statusBadgeFor(reservation.status),
      trailing: syncBadge,
      onTap: openDetailsOnTap ? onOpenDetail : null,
    );
  }

  static AppBadge statusBadgeFor(String status) {
    switch (status) {
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
