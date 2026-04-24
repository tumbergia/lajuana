import '../../../../../app/widgets/app_badge.dart';
import '../../../data/catalog_sync_status.dart';
import '../../domain/schedule.dart';
import '../../domain/schedule_status.dart';

AppBadge scheduleStatusBadgeFor(CatalogSchedule schedule) {
  if (!schedule.isActive) {
    return const AppBadge(
      label: 'Desactivada',
      tone: AppBadgeTone.neutral,
      uppercase: false,
    );
  }
  if (schedule.syncStatus == CatalogSyncStatus.pending) {
    return const AppBadge(
      label: 'Pendiente sync',
      tone: AppBadgeTone.warning,
      uppercase: false,
    );
  }
  if (schedule.syncStatus == CatalogSyncStatus.conflict ||
      schedule.syncStatus == CatalogSyncStatus.rejected) {
    return const AppBadge(
      label: 'Error sync',
      tone: AppBadgeTone.danger,
      uppercase: false,
    );
  }
  switch (schedule.status) {
    case CatalogScheduleStatus.open:
      return const AppBadge(
        label: 'Abierta',
        tone: AppBadgeTone.success,
        uppercase: false,
      );
    case CatalogScheduleStatus.closed:
      return const AppBadge(
        label: 'Cerrada',
        tone: AppBadgeTone.warning,
        uppercase: false,
      );
    case CatalogScheduleStatus.full:
      return const AppBadge(
        label: 'Completa',
        tone: AppBadgeTone.primary,
        uppercase: false,
      );
  }
}
