import 'package:flutter/material.dart';

import 'package:mobile/app/widgets/app_badge.dart';
import 'package:mobile/app/widgets/app_entity_row_card.dart';

import '../../domain/models/reservation_status.dart';
import '../../infrastructure/mappers/reservation_mapper.dart';
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
            : null;

    // Build subtitle with extra info if available
    String displaySubtitle = subtitle;
    if (reservation.participantCount != null) {
      final total = reservation.participantCount;
      final registered = reservation.registeredCount ?? 0;
      displaySubtitle += ' · $registered/$total';
    }

    return AppEntityRowCard(
      title: reservation.clientName,
      subtitle: displaySubtitle,
      selected: highlightIfPending && reservation.status == 'pendientes',
      badge: statusBadgeFor(reservation),
      trailing: syncBadge,
      onTap: openDetailsOnTap ? onOpenDetail : null,
    );
  }

  static AppBadge statusBadgeFor(ReservationRecord reservation) {
    // Use raw status if available for accurate badge colour
    final status = reservation.status;

    // Map legacy string statuses
    if (status == 'pendientes') {
      return const AppBadge(
        label: 'Pendiente',
        tone: AppBadgeTone.warning,
        uppercase: false,
      );
    }
    if (status == 'confirmadas') {
      return const AppBadge(
        label: 'Confirmada',
        tone: AppBadgeTone.primary,
        uppercase: false,
      );
    }
    if (status == 'finalizadas' || status == 'cerradas') {
      return const AppBadge(
        label: 'Finalizada',
        tone: AppBadgeTone.success,
        uppercase: false,
      );
    }

    // Use ReservationStatus-based badge if available
    if (reservation.statusRaw != null) {
      return AppBadge(
        label: reservationStatusLabel(reservation.statusRaw as dynamic),
        tone: reservationStatusToBadgeTone(reservation.statusRaw as dynamic),
        uppercase: false,
      );
    }

    return const AppBadge(
      label: 'Sin estado',
      tone: AppBadgeTone.neutral,
      uppercase: false,
    );
  }

  /// Legacy static helper for external components that pass string statuses.
  static AppBadge statusBadgeForLegacy(String status) {
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
