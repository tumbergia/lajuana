import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile/features/catalogs/data/catalog_sync_status.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';

AppBadge experienceStatusBadgeFor(CatalogExperience experience) {
  if (!experience.isActive) {
    return const AppBadge(
      label: 'Inactiva',
      tone: AppBadgeTone.neutral,
      uppercase: false,
    );
  }
  switch (experience.syncStatus) {
    case CatalogSyncStatus.pending:
      return const AppBadge(
        label: 'Pendiente sync',
        tone: AppBadgeTone.warning,
        uppercase: false,
      );
    case CatalogSyncStatus.conflict:
      return const AppBadge(
        label: 'Conflicto',
        tone: AppBadgeTone.danger,
        uppercase: false,
      );
    case CatalogSyncStatus.rejected:
      return const AppBadge(
        label: 'Rechazada',
        tone: AppBadgeTone.danger,
        uppercase: false,
      );
    case CatalogSyncStatus.synced:
      return const AppBadge(
        label: 'Activa',
        tone: AppBadgeTone.success,
        uppercase: false,
      );
  }
}
