import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/catalogs/experiences/presentation/controllers/experiences_controller.dart';

import 'fake_catalogs_repository.dart';
import 'fake_experience_repository.dart';

void main() {
  late FakeExperienceRepository experienceRepo;
  late FakeCatalogsRepository catalogsRepo;
  late ExperiencesController controller;

  setUp(() {
    experienceRepo = FakeExperienceRepository();
    catalogsRepo = FakeCatalogsRepository();
    controller = ExperiencesController(
      repository: experienceRepo,
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
    test('loads experiences from local repository', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.isInitialLoading, false);
      expect(controller.items, isNotEmpty);
      expect(controller.hasLocalData, true);
      expect(controller.error, isNull);
      expect(experienceRepo.listCallCount, 1);
    });

    test('loads empty when repository returns empty', () async {
      experienceRepo = FakeExperienceRepository(returnEmpty: true);
      controller = ExperiencesController(
        repository: experienceRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.items, isEmpty);
      expect(controller.hasLocalData, false);
    });

    test('handles error during load', () async {
      experienceRepo = FakeExperienceRepository(throwOnList: true);
      controller = ExperiencesController(
        repository: experienceRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.isInitialLoading, false);
      expect(controller.error, isNotNull);
    });

    test('triggers refreshFromServer when refreshServer is true', () async {
      await controller.loadLocalThenRefresh(refreshServer: true);

      // Give the unawaited refresh time to start
      await Future<void>.delayed(Duration.zero);

      expect(catalogsRepo.refreshExperiencesCallCount, 1);
    });
  });

  group('refreshFromServer', () {
    test('refreshes experiences from server', () async {
      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.items, isNotEmpty);
      expect(controller.error, isNull);
      expect(catalogsRepo.refreshExperiencesCallCount, 1);
      expect(
        experienceRepo.listCallCount,
        1,
      ); // list() called once during refresh
    });

    test('guards against double refresh', () async {
      controller.refreshFromServer(); // not awaited
      await controller.refreshFromServer();

      expect(catalogsRepo.refreshExperiencesCallCount, 1);
    });

    test('handles error during refresh', () async {
      catalogsRepo = FakeCatalogsRepository(throwOnRefresh: true);
      controller = ExperiencesController(
        repository: experienceRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.error, isNotNull);
    });
  });

  group('syncNow', () {
    test('syncs experiences', () async {
      await controller.syncNow();

      expect(controller.isSyncing, false);
      expect(controller.items, isNotEmpty);
      expect(catalogsRepo.syncNowCallCount, 1);
    });

    test('handles error during sync', () async {
      catalogsRepo = FakeCatalogsRepository(throwOnSync: true);
      controller = ExperiencesController(
        repository: experienceRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.syncNow();

      expect(controller.isSyncing, false);
      expect(controller.error, isNotNull);
    });
  });

  group('deactivate', () {
    test('deactivates experience and reloads', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);
      expect(controller.items, isNotEmpty);

      await controller.deactivate('exp-1');

      expect(controller.items, isNotEmpty);
      expect(experienceRepo.listCallCount, 2); // initial + after deactivate
    });
  });
}
