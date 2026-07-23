import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/catalogs/experiences/presentation/controllers/experiences_tab_controller.dart';

import 'fake_catalogs_repository.dart';
import 'fake_experience_repository.dart';

void main() {
  late FakeExperienceRepository experienceRepo;
  late FakeCatalogsRepository catalogsRepo;
  late ExperiencesTabController controller;

  setUp(() {
    experienceRepo = FakeExperienceRepository();
    catalogsRepo = FakeCatalogsRepository();
    controller = ExperiencesTabController(
      repository: experienceRepo,
      catalogsRepository: catalogsRepo,
    );
  });

  tearDown(() {
    controller.dispose();
  });

  group('loadLocalThenRefresh', () {
    test('loads experiences from local repository', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.loadState, ExperiencesTabLoadState.success);
      expect(controller.items, isNotEmpty);
      expect(controller.errorMessage, isEmpty);
      expect(experienceRepo.listCallCount, 1);
    });

    test(
      'uses syncing state when local is empty and server refresh runs',
      () async {
        experienceRepo = FakeExperienceRepository(emptyListCallsBeforeData: 1);
        catalogsRepo = FakeCatalogsRepository()
          ..refreshCompleter = Completer<void>();
        controller = ExperiencesTabController(
          repository: experienceRepo,
          catalogsRepository: catalogsRepo,
        );

        final loadFuture = controller.loadLocalThenRefresh(refreshServer: true);
        await Future<void>.delayed(Duration.zero);

        expect(controller.loadState, ExperiencesTabLoadState.syncing);
        expect(controller.items, isEmpty);

        catalogsRepo.refreshCompleter!.complete();
        while (controller.isRefreshing) {
          await Future<void>.delayed(Duration.zero);
        }
        await loadFuture;

        expect(controller.loadState, ExperiencesTabLoadState.success);
        expect(controller.items, isNotEmpty);
        expect(catalogsRepo.refreshExperiencesCallCount, 1);
      },
    );

    test(
      'uses empty state when local is empty and refresh is disabled',
      () async {
        experienceRepo = FakeExperienceRepository(returnEmpty: true);
        controller = ExperiencesTabController(
          repository: experienceRepo,
          catalogsRepository: catalogsRepo,
        );

        await controller.loadLocalThenRefresh(refreshServer: false);

        expect(controller.loadState, ExperiencesTabLoadState.empty);
        expect(controller.items, isEmpty);
      },
    );

    test('handles error during local load', () async {
      experienceRepo = FakeExperienceRepository(throwOnList: true);
      controller = ExperiencesTabController(
        repository: experienceRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.loadState, ExperiencesTabLoadState.error);
      expect(controller.errorMessage, isNotEmpty);
    });
  });

  group('refreshFromServer', () {
    test('refreshes experiences from server', () async {
      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.loadState, ExperiencesTabLoadState.success);
      expect(controller.items, isNotEmpty);
      expect(controller.errorMessage, isEmpty);
      expect(catalogsRepo.refreshExperiencesCallCount, 1);
    });

    test('keeps cached data when refresh fails', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);
      expect(controller.allItems, isNotEmpty);

      catalogsRepo = FakeCatalogsRepository(throwOnRefresh: true);
      final failingController = ExperiencesTabController(
        repository: experienceRepo,
        catalogsRepository: catalogsRepo,
      );
      addTearDown(failingController.dispose);

      await failingController.loadLocalThenRefresh(refreshServer: false);
      expect(failingController.allItems, isNotEmpty);

      await failingController.refreshFromServer();

      expect(
        failingController.loadState,
        ExperiencesTabLoadState.offlineFromCache,
      );
      expect(failingController.allItems, isNotEmpty);
      expect(failingController.errorMessage, isNotEmpty);
    });

    test('shows error when refresh fails without local cache', () async {
      catalogsRepo = FakeCatalogsRepository(throwOnRefresh: true);
      controller = ExperiencesTabController(
        repository: FakeExperienceRepository(returnEmpty: true),
        catalogsRepository: catalogsRepo,
      );

      await controller.refreshFromServer();

      expect(controller.loadState, ExperiencesTabLoadState.error);
      expect(controller.allItems, isEmpty);
    });

    test('guards against double refresh', () async {
      controller.refreshFromServer();
      await controller.refreshFromServer();

      expect(catalogsRepo.refreshExperiencesCallCount, 1);
    });
  });
}
