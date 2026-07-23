import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_domain/src/equines/equine.dart';
import 'package:mobile_domain/src/equines/equine_experience_fit.dart';
import 'package:mobile_domain/src/equines/equine_operational_status.dart';
import 'package:mobile_domain/src/equines/equine_timeline_entry.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile/features/equines/presentation/controllers/equines_controller.dart';

// ── Fake repository ──────────────────────────────────────────────────────

class FakeEquineRepository implements EquineRepository {
  List<Equine> equines = [];
  List<EquineTimelineEntry> timeline = [];
  DateTime? lastSyncedAt;
  bool throwOnList = false;
  bool throwOnTimeline = false;
  int listEquinesCallCount = 0;
  bool? lastIncludeDeleted;

  @override
  Future<List<Equine>> listEquines({
    String? operationalStatus,
    bool includeDeleted = false,
  }) async {
    listEquinesCallCount++;
    lastIncludeDeleted = includeDeleted;
    if (throwOnList) throw Exception('Network error');
    if (operationalStatus != null) {
      return equines
          .where((e) => e.operationalStatus.name == operationalStatus)
          .toList();
    }
    if (includeDeleted) return equines;
    return equines.where((e) => e.isActive).toList(growable: false);
  }

  @override
  Future<Equine> getEquineById(String equineId) async {
    return equines.firstWhere((e) => e.id == equineId);
  }

  @override
  Future<Equine> createEquine(Map<String, dynamic> data) async {
    throw UnimplementedError('Not needed for controller tests');
  }

  @override
  Future<Equine> updateEquine(
    String equineId,
    Map<String, dynamic> data,
  ) async {
    throw UnimplementedError('Not needed for controller tests');
  }

  @override
  Future<List<EquineTimelineEntry>> getEquineTimeline(String equineId) async {
    if (throwOnTimeline) throw Exception('Timeline error');
    return timeline;
  }

  @override
  Future<List<Equine>> listAvailableForReservation(String reservationId) async {
    throw UnimplementedError('Not needed for controller tests');
  }

  @override
  Future<Equine> deleteEquine(String equineId) async {
    throw UnimplementedError('Not needed for controller tests');
  }

  @override
  Future<Equine> restoreEquine(String equineId) async {
    throw UnimplementedError('Not needed for controller tests');
  }

  @override
  Future<DateTime?> getLastSyncedAt() async => lastSyncedAt;
}

// ── Helpers ──────────────────────────────────────────────────────────────

Equine _equine({
  required String id,
  required String name,
  EquineOperationalStatus status = EquineOperationalStatus.available,
  bool isAvailable = true,
  bool isActive = true,
}) {
  return Equine(
    id: id,
    name: name,
    operationalStatus: status,
    isAvailable: isAvailable,
    isActive: isActive,
  );
}

void main() {
  late FakeEquineRepository repo;
  late EquinesController controller;

  setUp(() {
    repo = FakeEquineRepository();
    controller = EquinesController(repository: repo);
  });

  tearDown(() {
    controller.dispose();
  });

  group('initial state', () {
    test('starts in idle state with empty records', () {
      expect(controller.loadState, EquinesLoadState.idle);
      expect(controller.records, isEmpty);
      expect(controller.selectedEquineId, isNull);
      expect(controller.selectedDetail, isNull);
    });

    test('subroute defaults to resumen', () {
      expect(controller.subroute, EquinesSubroute.resumen);
    });
  });

  group('loadEquines', () {
    test('transitions to loading then success', () async {
      repo.equines = [_equine(id: '1', name: 'Pegaso')];

      final states = <EquinesLoadState>[];
      controller.addListener(() {
        states.add(controller.loadState);
      });

      await controller.loadEquines();

      expect(controller.loadState, EquinesLoadState.success);
      expect(controller.records.length, 1);
      expect(controller.records.first.name, 'Pegaso');
    });

    test('shows empty state when no equines', () async {
      repo.equines = [];
      await controller.loadEquines();
      expect(controller.loadState, EquinesLoadState.empty);
    });

    test('shows error state on failure', () async {
      repo.throwOnList = true;
      await controller.loadEquines();
      expect(controller.loadState, EquinesLoadState.error);
      expect(controller.errorMessage, 'No se pudieron cargar los equinos.');
    });

    test('auto-selects first equine', () async {
      repo.equines = [
        _equine(id: '1', name: 'Alpha'),
        _equine(id: '2', name: 'Beta'),
      ];
      await controller.loadEquines();
      expect(controller.selectedEquineId, '1');
      expect(controller.selectedDetail, isNotNull);
    });
  });

  group('metrics', () {
    test('computes metrics correctly', () async {
      repo.equines = [
        _equine(
          id: '1',
          name: 'A',
          status: EquineOperationalStatus.available,
          isAvailable: true,
        ),
        _equine(
          id: '2',
          name: 'B',
          status: EquineOperationalStatus.available,
          isAvailable: true,
        ),
        _equine(
          id: '3',
          name: 'C',
          status: EquineOperationalStatus.resting,
          isAvailable: false,
        ),
        _equine(
          id: '4',
          name: 'D',
          status: EquineOperationalStatus.injured,
          isAvailable: false,
        ),
      ];
      await controller.loadEquines();
      final m = controller.metrics;
      expect(m.total, 4);
      expect(m.available, 2);
      expect(m.blocked, 1); // injured counts as blocked
    });

    test('metrics return zeros when empty', () {
      final m = controller.metrics;
      expect(m.total, 0);
      expect(m.available, 0);
      expect(m.blocked, 0);
    });
  });

  group('subroute filtering', () {
    test('resumen shows all records', () async {
      repo.equines = [
        _equine(id: '1', name: 'A', status: EquineOperationalStatus.available),
        _equine(id: '2', name: 'B', status: EquineOperationalStatus.injured),
      ];
      await controller.loadEquines();
      expect(controller.records.length, 2);
    });

    test('disponibilidad filters available', () async {
      repo.equines = [
        _equine(id: '1', name: 'A', status: EquineOperationalStatus.available),
        _equine(id: '2', name: 'B', status: EquineOperationalStatus.injured),
      ];
      await controller.loadEquines();
      controller.selectSubrouteByIndex(2); // Disponibilidad
      expect(controller.records.length, 1);
      expect(controller.records.first.name, 'A');
    });

    test('cuidado filters warning/danger', () async {
      repo.equines = [
        _equine(id: '1', name: 'A', status: EquineOperationalStatus.available),
        _equine(id: '2', name: 'B', status: EquineOperationalStatus.injured),
        _equine(id: '3', name: 'C', status: EquineOperationalStatus.resting),
      ];
      await controller.loadEquines();
      controller.selectSubrouteByIndex(3); // Cuidado
      expect(controller.records.length, 1);
      expect(controller.records.first.name, 'B');
    });
  });

  group('status filter', () {
    test('filters by operational status', () async {
      repo.equines = [
        _equine(id: '1', name: 'A', status: EquineOperationalStatus.available),
        _equine(id: '2', name: 'B', status: EquineOperationalStatus.resting),
        _equine(id: '3', name: 'C', status: EquineOperationalStatus.inService),
      ];
      await controller.loadEquines();
      controller.setStatusFilter(EquineOperationalStatus.resting);
      expect(controller.records.length, 1);
      expect(controller.records.first.name, 'B');
    });

    test('clearing filter shows all', () async {
      repo.equines = [
        _equine(id: '1', name: 'A', status: EquineOperationalStatus.available),
        _equine(id: '2', name: 'B', status: EquineOperationalStatus.resting),
      ];
      await controller.loadEquines();
      controller.setStatusFilter(EquineOperationalStatus.resting);
      expect(controller.records.length, 1);
      controller.setStatusFilter(null);
      expect(controller.records.length, 2);
    });
  });

  group('filter mode', () {
    test('loads deleted equines on initial fetch', () async {
      repo.equines = [
        _equine(id: '1', name: 'A'),
        _equine(id: '2', name: 'B', isActive: false),
      ];
      await controller.loadEquines();

      expect(repo.lastIncludeDeleted, true);
    });

    test('filters deleted equines locally without refetching', () async {
      repo.equines = [
        _equine(id: '1', name: 'A'),
        _equine(id: '2', name: 'B', isActive: false),
      ];
      await controller.loadEquines();
      final initialCallCount = repo.listEquinesCallCount;

      controller.setFilterMode('deleted');

      expect(repo.listEquinesCallCount, initialCallCount);
      expect(controller.records.length, 1);
      expect(controller.records.first.name, 'B');
    });

    test('filters by operational status locally without refetching', () async {
      repo.equines = [
        _equine(id: '1', name: 'A', status: EquineOperationalStatus.available),
        _equine(id: '2', name: 'B', status: EquineOperationalStatus.resting),
      ];
      await controller.loadEquines();
      final initialCallCount = repo.listEquinesCallCount;

      controller.setFilterMode('resting');

      expect(repo.listEquinesCallCount, initialCallCount);
      expect(controller.records.length, 1);
      expect(controller.records.first.name, 'B');
    });

    test('excludes deleted equines from non-deleted filters', () async {
      repo.equines = [
        _equine(id: '1', name: 'A'),
        _equine(id: '2', name: 'B', isActive: false),
      ];
      await controller.loadEquines();

      expect(controller.records.length, 1);
      expect(controller.records.first.name, 'A');
    });
  });

  group('selectEquine', () {
    test('selects equine and builds detail from memory', () async {
      repo.equines = [
        _equine(id: '1', name: 'Pegaso'),
        _equine(id: '2', name: 'Bucéfalo'),
      ];
      await controller.loadEquines();
      controller.selectEquine('2');
      expect(controller.selectedEquineId, '2');
      expect(controller.selectedDetail?.name, 'Bucéfalo');
    });
  });

  group('lastSyncedAt', () {
    test('loadLastSyncedAt reads from repository', () async {
      repo.lastSyncedAt = DateTime(2026, 6, 1, 10, 0);
      await controller.loadLastSyncedAt();
      expect(controller.lastSyncedAt, isNotNull);
      expect(controller.lastSyncedAt!.year, 2026);
    });

    test('handles null lastSyncedAt gracefully', () async {
      repo.lastSyncedAt = null;
      await controller.loadLastSyncedAt();
      expect(controller.lastSyncedAt, isNull);
    });
  });
}
