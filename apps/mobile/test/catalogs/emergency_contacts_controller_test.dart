import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/catalogs/emergency_contacts/presentation/controllers/emergency_contacts_controller.dart';

import 'fake_catalogs_repository.dart';
import 'fake_emergency_contacts_repository.dart';

void main() {
  late FakeEmergencyContactsRepository contactsRepo;
  late FakeCatalogsRepository catalogsRepo;
  late EmergencyContactsController controller;

  setUp(() {
    contactsRepo = FakeEmergencyContactsRepository();
    catalogsRepo = FakeCatalogsRepository();
    controller = EmergencyContactsController(
      repository: contactsRepo,
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
      expect(controller.error, isNull);
      expect(controller.items, isEmpty);
      expect(controller.hasLocalData, false);
    });
  });

  group('loadLocalThenRefresh', () {
    test('loads contacts from local repository', () async {
      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.isInitialLoading, false);
      expect(controller.items, isNotEmpty);
      expect(controller.hasLocalData, true);
      expect(controller.error, isNull);
      expect(contactsRepo.listCallCount, 1);
    });

    test('handles empty repository', () async {
      contactsRepo = FakeEmergencyContactsRepository(returnEmpty: true);
      controller = EmergencyContactsController(
        repository: contactsRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.items, isEmpty);
      expect(controller.hasLocalData, false);
    });

    test('handles error during load', () async {
      contactsRepo = FakeEmergencyContactsRepository(throwOnList: true);
      controller = EmergencyContactsController(
        repository: contactsRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.loadLocalThenRefresh(refreshServer: false);

      expect(controller.isInitialLoading, false);
      expect(controller.error, isNotNull);
    });

    test('triggers refreshFromServer when refreshServer is true', () async {
      await controller.loadLocalThenRefresh(refreshServer: true);

      await Future<void>.delayed(Duration.zero);

      expect(catalogsRepo.refreshContactsCallCount, 1);
    });
  });

  group('refreshFromServer', () {
    test('refreshes contacts from server', () async {
      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.items, isNotEmpty);
      expect(catalogsRepo.refreshContactsCallCount, 1);
      expect(
        contactsRepo.listCallCount,
        1,
      ); // list() called once during refresh
    });

    test('guards against double refresh', () async {
      controller.refreshFromServer(); // not awaited
      await controller.refreshFromServer();

      expect(catalogsRepo.refreshContactsCallCount, 1);
    });

    test('handles error during refresh', () async {
      catalogsRepo = FakeCatalogsRepository(throwOnRefresh: true);
      controller = EmergencyContactsController(
        repository: contactsRepo,
        catalogsRepository: catalogsRepo,
      );

      await controller.refreshFromServer();

      expect(controller.isRefreshing, false);
      expect(controller.error, isNotNull);
    });
  });
}
