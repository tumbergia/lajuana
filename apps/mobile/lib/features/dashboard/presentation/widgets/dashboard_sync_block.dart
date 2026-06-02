import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/reservations/presentation/models/reservation_view_models.dart';

class DashboardSyncBlock extends StatelessWidget {
  const DashboardSyncBlock({
    super.key,
    required this.authController,
    required this.reservations,
  });

  final AuthController authController;
  final List<ReservationRecord> reservations;

  @override
  Widget build(BuildContext context) {
    final hasSyncError = reservations.any((item) => item.hasSyncError);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppEntityRowCard(
          title: 'Cambios pendientes',
          subtitle: authController.hasPendingSync
              ? 'Hay cambios locales por enviar'
              : 'No hay cambios pendientes',
          badge: AppBadge(
            label: authController.hasPendingSync ? 'Pendiente' : 'OK',
            tone: authController.hasPendingSync
                ? AppBadgeTone.warning
                : AppBadgeTone.success,
            uppercase: false,
          ),
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: 'Conflictos de sincronizacion',
          subtitle: hasSyncError
              ? 'Hay reservas con error de sync'
              : 'Sin conflictos detectados',
          badge: AppBadge(
            label: hasSyncError ? 'Revisar' : 'Limpio',
            tone: hasSyncError ? AppBadgeTone.danger : AppBadgeTone.success,
            uppercase: false,
          ),
        ),
      ],
    );
  }
}
