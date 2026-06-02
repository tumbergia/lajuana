import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/catalogs/schedules/presentation/controllers/schedules_controller.dart';

import 'fake_catalogs_repository.dart';
import 'fake_schedule_repository.dart';

void main() {
  late FakeScheduleRepository scheduleRepo;
  late FakeCatalogsRepository catalogsRepo;
  late SchedulesController controller;

  setUp(() {
    scheduleRepo = FakeScheduleRepository();
    catalogsRepo = FakeCatalogsRepository();
    controller = SchedulesController(
      repository: scheduleRepo,
      catalogsRepository: catalogsRepo,
    );
  });

  tearDown(() {
    controller.dispose();
  });

  group('initial state', () {
    test('starts with default values', () {
      expect(controller.isInitialLoading, false);
      expect(controller.isRefreshing, false);
      expect(controller.isSyncing, false);
      expect(controller.error, isNull);
      expect(controller.items, isEmpty);
      expect(controller.hasLocalData, false);
    });
  });

  group('loadLocalThenRefresh', () {
    test('loads schedules from local repository', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.isInitialLoading, false);
      expect(controller.items, isNotEmpty);
      expect(controller.hasLocalData, true);
      expect(controller.error, isNull);
      expect(scheduleRepo.listCallCount, 1);
    });

    test('handles empty repository', () async {
      scheduleRepo = FakeScheduleRepository(returnEmpty: true);
      controller = SchedulesController(
        repository: scheduleRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.items, isEmpty);
      expect(controller.hasLocalData, false);
    });

    test('handles error during load', () async {
      scheduleRepo = FakeScheduleRepository(throwOnList: true);
      controller = SchedulesController(
        repository: scheduleRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.isInitialLoading, false);
      expect(controller.error, isNotNull);
    });
  });

  group('refreshFromServer', () {
    test('refreshes from server', () async {
      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.items, isNotEmpty);
      expect(catalogsRepo.refreshSchedulesCallCount, 1);
    });

    test('guards against double refresh', () async {
      controller.refreshFromServer(); // not awaited
      await controller.refreshFromServer();

      expect(catalogsRepo.refreshSchedulesCallCount, 1);
    });

    test('handles error during refresh', () async {
      catalogsRepo = FakeCatalogsRepository(throwOnRefresh: true);
      controller = SchedulesController(
        repository: scheduleRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.error, isNotNull);
    });
  });

  group('syncNow', () {
    test('syncs schedules', () async {
      await controller.syncNow();

      expect(controller.isSyncing, false);
      expect(controller.items, isNotEmpty);
      expect(catalogsRepo.syncNowCallCount, 1);
    });

    test('handles error during sync', () async {
      catalogsRepo = FakeCatalogsRepository(throwOnSync: true);
      controller = SchedulesController(
        repository: scheduleRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.syncNow();

      expect(controller.isSyncing, false);
      expect(controller.error, isNotNull);
    });
  });

  group('deactivate', () {
    test('deactivates schedule and reloads', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);
      expect(controller.items, isNotEmpty);

      await controller.deactivate('sched-1');

      expect(controller.items, isNotEmpty);
      expect(scheduleRepo.listCallCount, 2);
    });
  });
}
