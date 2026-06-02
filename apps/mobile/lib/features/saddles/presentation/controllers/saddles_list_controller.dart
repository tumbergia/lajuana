import 'package:flutter/foundation.dart';

import 'package:mobile_domain/src/saddles/saddles_repository.dart';
import 'package:mobile/features/saddles/infrastructure/mappers/saddle_mapper.dart';
import 'package:mobile/features/saddles/presentation/models/saddle_view_models.dart';

enum SaddlesLoadState {
  idle,
  loading,
  refreshing,
  success,
  empty,
  error,
  offlineFromCache,
}

class SaddlesListController extends ChangeNotifier {
  SaddlesListController({required SaddlesRepository repository})
      : _repository = repository;

  final SaddlesRepository _repository;

  SaddlesLoadState state = SaddlesLoadState.idle;
  List<SaddleRecord> items = const <SaddleRecord>[];
  String searchQuery = '';
  bool? showOnlyAvailable; // null = all, true = available, false = unavailable
  bool includeDeleted = false;
  String? errorCode;
  String? errorMessage;
  DateTime? lastSyncAt;

  List<SaddleRecord> _allItems = const <SaddleRecord>[];

  Future<void> loadInitial() async {
    state = SaddlesLoadState.loading;
    errorCode = null;
    errorMessage = null;
    notifyListeners();

    try {
      await _fetchFromRemote(isRefresh: false);
    } catch (e) {
      state = SaddlesLoadState.error;
      errorCode = 'network.unavailable';
      errorMessage = 'No se pudieron cargar las sillas.';
      notifyListeners();
    }
  }

  Future<void> refresh() async {
    if (state == SaddlesLoadState.loading) return;
    state = SaddlesLoadState.refreshing;
    errorCode = null;
    errorMessage = null;
    notifyListeners();

    try {
      await _fetchFromRemote(isRefresh: true);
    } catch (e) {
      errorCode = 'network.unavailable';
      errorMessage = 'No se pudo actualizar.';
      if (_allItems.isEmpty) {
        state = SaddlesLoadState.error;
      } else {
        state = SaddlesLoadState.offlineFromCache;
      }
      notifyListeners();
    }
  }

  Future<void> _fetchFromRemote({required bool isRefresh}) async {
    final domainItems = await _repository.listSaddles(
      includeDeleted: includeDeleted,
    );
    lastSyncAt = DateTime.now();

    if (domainItems.isEmpty) {
      _allItems = const <SaddleRecord>[];
      items = const <SaddleRecord>[];
      state = SaddlesLoadState.empty;
      notifyListeners();
      return;
    }

    _allItems = domainItems.map((item) => listItemToRecord(item)).toList();
    _applyLocalFilters();
    state = SaddlesLoadState.success;
    notifyListeners();
  }

  void setIncludeDeleted(bool value) {
    if (includeDeleted == value) return;
    includeDeleted = value;
    refresh();
  }

  void setShowOnlyAvailable(bool? value) {
    if (showOnlyAvailable == value) return;
    showOnlyAvailable = value;
    _applyLocalFilters();
    notifyListeners();
  }

  void setSearchQuery(String query) {
    searchQuery = query;
    _applyLocalFilters();
    notifyListeners();
  }

  void _applyLocalFilters() {
    var result = _allItems;

    // When showing deleted, filter locally to only deleted items
    if (includeDeleted) {
      result = result
          .where((item) => item.isDeleted)
          .toList(growable: false);
    }

    // Apply availability filter
    if (showOnlyAvailable != null) {
      result = result
          .where((item) => item.isAvailable == showOnlyAvailable)
          .toList(growable: false);
    }

    // Apply search query
    if (searchQuery.trim().isNotEmpty) {
      final q = searchQuery.toLowerCase().trim();
      result = result
          .where((item) =>
              item.code.toLowerCase().contains(q) ||
              item.name.toLowerCase().contains(q))
          .toList(growable: false);
    }

    items = result;
  }

  /// Whether we have ever loaded any items (even if filtered empty).
  bool get hasAnyRecords => _allItems.isNotEmpty;

  void reset() {
    showOnlyAvailable = null;
    includeDeleted = false;
    searchQuery = '';
    errorCode = null;
    errorMessage = null;
    state = SaddlesLoadState.idle;
    notifyListeners();
  }
}
