import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/saddles/presentation/controllers/saddles_list_controller.dart';

import 'fake_saddles_repository.dart';

void main() {
  late FakeSaddlesRepository repository;
  late SaddlesListController controller;

  setUp(() {
    repository = FakeSaddlesRepository();
    controller = SaddlesListController(repository: repository);
  });

  tearDown(() {
    controller.dispose();
  });

  group('initial state', () {
    test('starts idle with empty items', () {
      expect(controller.state, SaddlesLoadState.idle);
      expect(controller.items, isEmpty);
      expect(controller.searchQuery, '');
      expect(controller.showOnlyAvailable, isNull);
      expect(controller.includeDeleted, false);
      expect(controller.errorCode, isNull);
      expect(controller.errorMessage, isNull);
    });
  });

  group('loadInitial', () {
    test('transitions to loading then success with items', () async {
      expect(controller.state, SaddlesLoadState.idle);

      await controller.loadInitial();

      expect(controller.state, SaddlesLoadState.success);
      expect(controller.items, isNotEmpty);
      expect(controller.lastSyncAt, isNotNull);
      expect(repository.listSaddlesCallCount, 1);
    });

    test('handles empty repository', () async {
      repository = FakeSaddlesRepository(returnEmpty: true);
      controller = SaddlesListController(repository: repository);

      await controller.loadInitial();

      expect(controller.state, SaddlesLoadState.empty);
      expect(controller.items, isEmpty);
    });

    test('handles network error', () async {
      repository = FakeSaddlesRepository(throwOnList: true);
      controller = SaddlesListController(repository: repository);

      await controller.loadInitial();

      expect(controller.state, SaddlesLoadState.error);
      expect(controller.errorCode, isNotNull);
      expect(controller.errorMessage, isNotNull);
    });
  });

  group('refresh', () {
    test('transitions to refreshing then success', () async {
      await controller.loadInitial();
      expect(controller.state, SaddlesLoadState.success);

      await controller.refresh();

      expect(controller.state, SaddlesLoadState.success);
      expect(controller.items, isNotEmpty);
    });

    test('does nothing if already loading', () async {
      // By not awaiting loadInitial, state stays loading
      controller.state = SaddlesLoadState.loading;

      await controller.refresh();

      // State should remain loading since guard prevents it
      expect(controller.state, SaddlesLoadState.loading);
    });

    test('shows error when refresh fails with no cached data', () async {
      repository = FakeSaddlesRepository(throwOnList: true);
      controller = SaddlesListController(repository: repository);

      await controller.refresh();

      expect(controller.state, SaddlesLoadState.error);
      expect(controller.errorCode, 'network.unavailable');
    });

    test(
      'shows offlineFromCache when refresh fails with cached data',
      () async {
        await controller.loadInitial();
        expect(controller.state, SaddlesLoadState.success);
        expect(controller.items, isNotEmpty);

        repository.throwOnList = true;

        await controller.refresh();

        expect(controller.state, SaddlesLoadState.offlineFromCache);
        // Items should still be available from cached data
        expect(controller.items, isNotEmpty);
      },
    );
  });

  group('search', () {
    test('filters items by code', () async {
      await controller.loadInitial();

      controller.setSearchQuery('MON-001');

      expect(controller.items.length, 1);
      expect(controller.items.first.code, 'MON-001');
    });

    test('filters items by name (case insensitive)', () async {
      await controller.loadInitial();

      controller.setSearchQuery('clásica');

      expect(controller.items, isNotEmpty);
    });

    test('shows all items when query is cleared', () async {
      await controller.loadInitial();

      controller.setSearchQuery('NONEXISTENT');
      expect(controller.items, isEmpty);

      controller.setSearchQuery('');
      expect(controller.items, isNotEmpty);
    });
  });

  group('availability filter', () {
    test('shows only available items', () async {
      await controller.loadInitial();

      controller.setShowOnlyAvailable(true);

      expect(controller.items, isNotEmpty);
      expect(controller.items.every((s) => s.isAvailable), true);
    });

    test('shows only unavailable items', () async {
      await controller.loadInitial();

      controller.setShowOnlyAvailable(false);

      expect(controller.items, isNotEmpty);
      expect(controller.items.every((s) => !s.isAvailable), true);
    });

    test('shows all when filter is cleared', () async {
      await controller.loadInitial();

      controller.setShowOnlyAvailable(true);
      expect(controller.items.every((s) => s.isAvailable), true);

      controller.setShowOnlyAvailable(null);
      expect(controller.items, isNotEmpty);
    });
  });

  group('include deleted', () {
    test('loads deleted items on initial fetch', () async {
      await controller.loadInitial();

      expect(repository.lastIncludeDeleted, true);
    });

    test('filters deleted items locally without refetching', () async {
      await controller.loadInitial();
      final initialCallCount = repository.listSaddlesCallCount;

      controller.setIncludeDeleted(true);

      expect(repository.listSaddlesCallCount, initialCallCount);
      expect(controller.includeDeleted, true);
      expect(controller.items, isNotEmpty);
      expect(controller.items.every((s) => s.isDeleted), true);
    });

    test('excludes deleted items from active filters', () async {
      await controller.loadInitial();

      expect(controller.items.every((s) => !s.isDeleted), true);
    });
  });

  group('hasAnyRecords', () {
    test('returns true after successful load', () async {
      await controller.loadInitial();
      expect(controller.hasAnyRecords, true);
    });

    test('returns false before loading', () async {
      expect(controller.hasAnyRecords, false);
    });
  });

  group('reset', () {
    test('resets filters and state to initial values', () async {
      await controller.loadInitial();
      expect(controller.items, isNotEmpty);

      controller.reset();

      expect(controller.state, SaddlesLoadState.idle);
      // items are NOT cleared (internal _allItems persists)
      expect(controller.items, isNotEmpty);
      expect(controller.searchQuery, '');
      expect(controller.showOnlyAvailable, isNull);
      expect(controller.includeDeleted, false);
      expect(controller.errorCode, isNull);
      expect(controller.errorMessage, isNull);
    });
  });

  group('dispose', () {
    test('does not notify listeners after dispose', () {
      final localController = SaddlesListController(repository: repository);
      var notifyCount = 0;
      localController.addListener(() => notifyCount++);
      localController.dispose();

      localController.setSearchQuery('test');

      expect(notifyCount, 0);
    });
  });
}
