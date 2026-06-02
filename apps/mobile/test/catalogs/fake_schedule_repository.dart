import 'package:mobile/features/catalogs/schedules/data/schedule_repository.dart';
import 'package:mobile/features/catalogs/schedules/domain/schedule.dart';
import 'package:mobile/features/catalogs/schedules/domain/schedule_status.dart';

import 'data/catalog_sync_status_helpers.dart';
import 'fake_catalogs_repository.dart';

/// Fake [ScheduleRepository] for testing [SchedulesController].
class FakeScheduleRepository extends ScheduleRepository {
  FakeScheduleRepository({
    this.returnEmpty = false,
    this.throwOnList = false,
    this.throwOnDeactivate = false,
  }) : super(FakeCatalogsRepository());

  final bool returnEmpty;
  final bool throwOnList;
  final bool throwOnDeactivate;

  int listCallCount = 0;

  static final _sampleSchedule = CatalogSchedule(
    id: 'sched-1',
    experienceId: 'exp-1',
    date: '2026-06-15',
    startTime: '08:00:00',
    isActive: true,
    capacityTotal: 10,
    reservedSlots: 3,
    internalSlots: 1,
    blockedSlots: 0,
    availableSlots: 6,
    status: CatalogScheduleStatus.open,
    customRequestOnly: false,
    syncStatus: catalogSyncStatusSynced,
  );

  @override
  Future<List<CatalogSchedule>> list() async {
    listCallCount++;
    if (throwOnList) throw Exception('List error');
    if (returnEmpty) return [];
    return [_sampleSchedule];
  }

  @override
  Future<void> deactivate(String id) async {
    if (throwOnDeactivate) throw Exception('Deactivate error');
  }
}
