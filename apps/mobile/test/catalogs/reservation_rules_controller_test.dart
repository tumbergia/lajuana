import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/catalogs/reservation_rules/presentation/controllers/reservation_rules_controller.dart';

import 'fake_catalogs_repository.dart';
import 'fake_reservation_rules_repository.dart';

void main() {
  late FakeReservationRulesRepository rulesRepo;
  late FakeCatalogsRepository catalogsRepo;
  late ReservationRulesController controller;

  setUp(() {
    rulesRepo = FakeReservationRulesRepository();
    catalogsRepo = FakeCatalogsRepository();
    controller = ReservationRulesController(
      repository: rulesRepo,
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
      expect(controller.rules, isNull);
      expect(controller.hasLocalData, false);
    });
  });

  group('loadLocalThenRefresh', () {
    test('loads rules from local repository', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.isInitialLoading, false);
      expect(controller.rules, isNotNull);
      expect(controller.hasLocalData, true);
      expect(controller.error, isNull);
      expect(rulesRepo.getCallCount, 1);
    });

    test('handles error during load', () async {
      rulesRepo = FakeReservationRulesRepository(throwOnGet: true);
      controller = ReservationRulesController(
        repository: rulesRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.isInitialLoading, false);
      expect(controller.error, isNotNull);
    });

    test('triggers refreshFromServer when refreshServer is true', () async {
      await controller.loadLocalThenRefresh(refreshServer: true);

      await Future<void>.delayed(Duration.zero);

      expect(catalogsRepo.refreshRulesCallCount, 1);
    });
  });

  group('refreshFromServer', () {
    test('refreshes rules from server', () async {
      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.rules, isNotNull);
      expect(catalogsRepo.refreshRulesCallCount, 1);
      expect(rulesRepo.getCallCount, 1); // get() called once during refresh
    });

    test('guards against double refresh', () async {
      controller.refreshFromServer(); // not awaited
      await controller.refreshFromServer();

      expect(catalogsRepo.refreshRulesCallCount, 1);
    });

    test('handles error during refresh', () async {
      catalogsRepo = FakeCatalogsRepository(throwOnRefresh: true);
      controller = ReservationRulesController(
        repository: rulesRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.error, isNotNull);
    });
  });

  group('update', () {
    test('updates rules and reloads', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);
      expect(controller.rules, isNotNull);

      await controller.update(
        minDaysInAdvance: 3,
        requirePaymentProofForConfirmation: true,
      );

      expect(controller.rules, isNotNull);
      expect(rulesRepo.updateCallCount, 1);
      expect(rulesRepo.getCallCount, 2); // initial + after update
    });

    test('handles error during update', () async {
      rulesRepo = FakeReservationRulesRepository(throwOnUpdate: true);
      controller = ReservationRulesController(
        repository: rulesRepo,
        catalogsRepository: catalogsRepo,
      );

      await expectLater(
        () => controller.update(
          minDaysInAdvance: 3,
          requirePaymentProofForConfirmation: true,
        ),
        throwsA(isA<Exception>()),
      );
    });
  });

  group('syncNow', () {
    test('syncs rules', () async {
      await controller.syncNow();

      expect(controller.isSyncing, false);
      expect(controller.rules, isNotNull);
      expect(catalogsRepo.syncNowCallCount, 1);
    });

    test('handles error during sync', () async {
      catalogsRepo = FakeCatalogsRepository(throwOnSync: true);
      controller = ReservationRulesController(
        repository: rulesRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.syncNow();

      expect(controller.isSyncing, false);
      expect(controller.error, isNotNull);
    });
  });
}
