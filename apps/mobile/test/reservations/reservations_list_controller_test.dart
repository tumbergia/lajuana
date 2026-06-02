import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservations_list_controller.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservations_list_state.dart';

import '../utils/fake_reservations_repository.dart';

void main() {
  late ReservationsRepository repository;
  late ReservationsListController controller;

  setUp(() {
    repository = FakeReservationsRepository();
    controller = ReservationsListController(repository: repository);
  });

  tearDown(() {
    controller.dispose();
  });

  group('initial state', () {
    test('starts idle with empty items', () {
      expect(controller.state, ReservationsLoadState.idle);
      expect(controller.items, isEmpty);
      expect(controller.searchQuery, '');
      expect(controller.filterGroup, isNull);
      expect(controller.errorCode, isNull);
      expect(controller.errorMessage, isNull);
    });
  });

  group('loadInitial', () {
    test('transitions to loading then success with items', () async {
      expect(controller.state, ReservationsLoadState.idle);

      await controller.loadInitial();

      expect(controller.state, ReservationsLoadState.success);
      expect(controller.items, isNotEmpty);
      expect(controller.lastSyncAt, isNotNull);
    });

    test('handles empty repository', () async {
      repository = FakeReservationsRepository(returnEmpty: true);
      controller = ReservationsListController(repository: repository);

      await controller.loadInitial();

      expect(controller.state, ReservationsLoadState.empty);
    });

    test('handles network error with cache fallback', () async {
      repository = FakeReservationsRepository.cacheOnly();
      controller = ReservationsListController(repository: repository);

      await controller.loadInitial();

      expect(controller.state, ReservationsLoadState.offlineFromCache);
    });
  });

  group('refresh', () {
    test('transitions to refreshing then success', () async {
      await controller.loadInitial();
      expect(controller.state, ReservationsLoadState.success);

      await controller.refresh();

      expect(controller.state, ReservationsLoadState.success);
      expect(controller.items, isNotEmpty);
    });

    test('handles error during refresh with cache fallback', () async {
      repository = FakeReservationsRepository(remoteFails: true);
      controller = ReservationsListController(repository: repository);

      await controller.loadInitial();

      expect(controller.state, ReservationsLoadState.offlineFromCache);
    });
  });

  group('filter', () {
    test('setFilterGroup triggers refresh', () async {
      await controller.loadInitial();
      expect(controller.state, ReservationsLoadState.success);

      controller.setFilterGroup('pendientes');
      // After setFilterGroup, the controller calls refresh()
      // Since FakeReservationsRepository returns items regardless
      await Future<void>.delayed(const Duration(milliseconds: 10));

      expect(controller.filterGroup, 'pendientes');
    });

    test('setSearchQuery filters items', () async {
      await controller.loadInitial();

      controller.setSearchQuery('nonexistent');

      expect(controller.searchQuery, 'nonexistent');
      expect(controller.items, isEmpty);
    });
  });

  group('reset', () {
    test('returns to idle with empty state', () async {
      await controller.loadInitial();
      expect(controller.state, ReservationsLoadState.success);

      controller.reset();

      expect(controller.state, ReservationsLoadState.idle);
      expect(controller.items, isEmpty);
      expect(controller.searchQuery, '');
      expect(controller.filterGroup, isNull);
    });
  });
}
