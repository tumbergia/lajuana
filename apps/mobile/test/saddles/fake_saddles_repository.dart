import 'package:mobile/features/saddles/domain/models/saddle_list_item.dart';
import 'package:mobile/features/saddles/domain/repositories/saddles_repository.dart';

/// Fake [SaddlesRepository] for testing [SaddlesListController].
///
/// Configurable via parameters:
/// - [returnEmpty] — returns empty list from [listSaddles]
/// - [throwOnList] — [listSaddles] throws on remote fetch
/// - [throwOnGet] — [getSaddleById] throws
class FakeSaddlesRepository implements SaddlesRepository {
  FakeSaddlesRepository({
    this.returnEmpty = false,
    this.throwOnList = false,
    this.throwOnGet = false,
  });

  final bool returnEmpty;
  bool throwOnList;
  final bool throwOnGet;

  int listSaddlesCallCount = 0;
  bool? lastIncludeDeleted;

  static final _sampleSaddle = SaddleListItem(
    id: 'saddle-1',
    code: 'MON-001',
    name: 'Montura Inglesa Clásica',
    isAvailable: true,
  );

  static final _sampleDeletedSaddle = SaddleListItem(
    id: 'saddle-2',
    code: 'MON-002',
    name: 'Montura Vaquera',
    isAvailable: false,
    deletedAt: DateTime(2026, 5, 1),
  );

  static final _sampleUnavailableSaddle = SaddleListItem(
    id: 'saddle-3',
    code: 'MON-003',
    name: 'Montura Dany',
    isAvailable: false,
  );

  List<SaddleListItem> get _items {
    if (returnEmpty) return [];
    return [_sampleSaddle, _sampleDeletedSaddle, _sampleUnavailableSaddle];
  }

  @override
  Future<List<SaddleListItem>> listSaddles({
    bool includeDeleted = false,
  }) async {
    listSaddlesCallCount++;
    lastIncludeDeleted = includeDeleted;
    if (throwOnList) throw Exception('Network error');
    final items = _items;
    if (includeDeleted) return items;
    return items.where((s) => !s.isDeleted).toList(growable: false);
  }

  @override
  Future<SaddleListItem> getSaddleById(String saddleId) async {
    if (throwOnGet) throw Exception('Not found');
    return _sampleSaddle;
  }

  @override
  Future<SaddleListItem> createSaddle({
    required String code,
    String? name,
    bool isAvailable = true,
    String? notes,
  }) async {
    return SaddleListItem(
      id: 'new-saddle',
      code: code,
      name: name,
      isAvailable: isAvailable,
      notes: notes,
    );
  }

  @override
  Future<SaddleListItem> updateSaddle({
    required String saddleId,
    String? code,
    String? name,
    bool? isAvailable,
    String? notes,
  }) async {
    return SaddleListItem(
      id: saddleId,
      code: code ?? _sampleSaddle.code,
      name: name ?? _sampleSaddle.name,
      isAvailable: isAvailable ?? _sampleSaddle.isAvailable,
      notes: notes,
    );
  }

  @override
  Future<SaddleListItem> deleteSaddle(String saddleId) async {
    return SaddleListItem(
      id: saddleId,
      code: 'DEL-001',
      name: 'Deleted Saddle',
      isAvailable: false,
      deletedAt: DateTime.now(),
    );
  }

  @override
  Future<SaddleListItem> restoreSaddle(String saddleId) async {
    return SaddleListItem(
      id: saddleId,
      code: 'RST-001',
      name: 'Restored Saddle',
      isAvailable: true,
    );
  }
}
