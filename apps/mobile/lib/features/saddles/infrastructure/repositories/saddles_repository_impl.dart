import '../../domain/models/saddle_list_item.dart';
import '../../domain/repositories/saddles_repository.dart';
import '../mappers/saddle_mapper.dart';
import '../remote/saddles_api_client.dart';

class SaddlesRepositoryImpl implements SaddlesRepository {
  SaddlesRepositoryImpl({required SaddlesApiClient apiClient})
      : _apiClient = apiClient;

  final SaddlesApiClient _apiClient;

  // In-memory cache
  List<SaddleListItem>? _cachedItems;

  @override
  Future<List<SaddleListItem>> listSaddles({bool includeDeleted = false}) async {
    try {
      final dtos = await _apiClient.listSaddles(includeDeleted: includeDeleted);
      final items = dtos.map((d) => dtoToListItem(d)).toList(growable: false);
      _cachedItems = items;
      return items;
    } catch (_) {
      if (_cachedItems != null) return _cachedItems!;
      rethrow;
    }
  }

  @override
  Future<SaddleListItem> getSaddleById(String saddleId) async {
    final dto = await _apiClient.getSaddleById(saddleId);
    return dtoToListItem(dto);
  }

  @override
  Future<SaddleListItem> deleteSaddle(String saddleId) async {
    final dto = await _apiClient.deleteSaddle(saddleId);
    final item = dtoToListItem(dto);
    // Update cache: remove from list
    final cached = _cachedItems;
    if (cached != null) {
      _cachedItems = cached
          .where((existing) => existing.id != saddleId)
          .toList(growable: false);
    }
    return item;
  }

  @override
  Future<SaddleListItem> restoreSaddle(String saddleId) async {
    final dto = await _apiClient.restoreSaddle(saddleId);
    final item = dtoToListItem(dto);
    // Update cache: add back to list
    final cached = _cachedItems;
    if (cached != null) {
      _cachedItems = [item, ...cached];
    }
    return item;
  }

  @override
  Future<SaddleListItem> createSaddle({
    required String code,
    String? name,
    bool isAvailable = true,
    String? notes,
  }) async {
    final payload = <String, dynamic>{
      'code': code,
      if (name != null) 'name': name,
      'is_available': isAvailable,
      if (notes != null) 'notes': notes,
    };
    final dto = await _apiClient.createSaddle(payload);
    final item = dtoToListItem(dto);
    // Update cache
    final cached = _cachedItems;
    if (cached != null) {
      _cachedItems = [item, ...cached];
    }
    return item;
  }

  @override
  Future<SaddleListItem> updateSaddle({
    required String saddleId,
    String? code,
    String? name,
    bool? isAvailable,
    String? notes,
  }) async {
    final payload = <String, dynamic>{};
    if (code != null) payload['code'] = code;
    if (name != null) payload['name'] = name;
    if (isAvailable != null) payload['is_available'] = isAvailable;
    if (notes != null) payload['notes'] = notes;

    final dto = await _apiClient.updateSaddle(saddleId, payload);
    final item = dtoToListItem(dto);
    // Update cache
    final cached = _cachedItems;
    if (cached != null) {
      _cachedItems = cached.map((existing) {
        return existing.id == saddleId ? item : existing;
      }).toList(growable: false);
    }
    return item;
  }
}
