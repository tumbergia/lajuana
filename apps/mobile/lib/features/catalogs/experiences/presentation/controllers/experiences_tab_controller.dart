import 'dart:async' show unawaited;

import 'package:flutter/foundation.dart';

import 'package:mobile/features/catalogs/data/catalogs_repository.dart';
import 'package:mobile/features/catalogs/experiences/data/experience_repository.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';

enum ExperiencesTabLoadState {
  idle,
  loading,
  success,
  empty,
  syncing,
  error,
  offlineFromCache,
}

class ExperiencesTabController extends ChangeNotifier {
  ExperiencesTabController({
    required ExperienceRepository repository,
    required CatalogsRepository catalogsRepository,
  }) : _repository = repository,
       _catalogsRepository = catalogsRepository;

  final ExperienceRepository _repository;
  final CatalogsRepository _catalogsRepository;

  ExperiencesTabLoadState _loadState = ExperiencesTabLoadState.idle;
  String _errorMessage = '';
  List<CatalogExperience> _items = const [];
  List<CatalogExperience> _allItems = const [];
  String _searchQuery = '';
  bool _isRefreshing = false;

  ExperiencesTabLoadState get loadState => _loadState;
  String get errorMessage => _errorMessage;
  List<CatalogExperience> get items => _items;
  List<CatalogExperience> get allItems => _allItems;
  String get searchQuery => _searchQuery;
  bool get isRefreshing => _isRefreshing;

  List<CatalogExperience> get _filteredItems {
    final q = _searchQuery.trim().toLowerCase();
    if (q.isEmpty) return _allItems;
    return _allItems.where((e) {
      return e.name.toLowerCase().contains(q) ||
          e.slug.toLowerCase().contains(q) ||
          (e.subtitle?.toLowerCase() ?? '').contains(q);
    }).toList();
  }

  void setSearchQuery(String value) {
    _searchQuery = value;
    _applyFilter();
    notifyListeners();
  }

  /// Loads from local SQLite then triggers a background server refresh.
  Future<void> loadLocalThenRefresh({bool refreshServer = true}) async {
    _loadState = ExperiencesTabLoadState.loading;
    _errorMessage = '';
    notifyListeners();

    try {
      final experiences = await _repository.list(includeInactive: true);
      if (experiences.isEmpty) {
        _allItems = const [];
        _items = const [];
        _loadState = refreshServer
            ? ExperiencesTabLoadState.syncing
            : ExperiencesTabLoadState.empty;
      } else {
        _allItems = experiences;
        _applyFilter();
        _loadState = ExperiencesTabLoadState.success;
      }
    } catch (e) {
      _errorMessage = e.toString();
      _loadState = ExperiencesTabLoadState.error;
    }
    notifyListeners();

    if (refreshServer) {
      unawaited(refreshFromServer());
    }
  }

  /// Simple local-only load (used after returning from detail/edit).
  Future<void> loadExperiences() async {
    _loadState = ExperiencesTabLoadState.loading;
    _errorMessage = '';
    notifyListeners();

    try {
      final experiences = await _repository.list(includeInactive: true);
      if (experiences.isEmpty) {
        _allItems = const [];
        _items = const [];
        _loadState = ExperiencesTabLoadState.empty;
      } else {
        _allItems = experiences;
        _applyFilter();
        _loadState = ExperiencesTabLoadState.success;
      }
    } catch (e) {
      _errorMessage = e.toString();
      _loadState = ExperiencesTabLoadState.error;
    }
    notifyListeners();
  }

  /// Pulls latest experiences from server (push handled post-mutation / autoSync).
  Future<void> refreshFromServer() async {
    if (_isRefreshing) return;
    _isRefreshing = true;
    _errorMessage = '';
    notifyListeners();

    try {
      await _catalogsRepository.refreshExperiencesFromServer();
      final experiences = await _repository.list(includeInactive: true);
      _allItems = experiences;
      if (experiences.isEmpty) {
        _items = const [];
        _loadState = ExperiencesTabLoadState.empty;
      } else {
        _applyFilter();
        _loadState = ExperiencesTabLoadState.success;
      }
    } catch (e) {
      _errorMessage = e.toString();
      if (_allItems.isNotEmpty) {
        _applyFilter();
        _loadState = ExperiencesTabLoadState.offlineFromCache;
      } else {
        _loadState = ExperiencesTabLoadState.error;
      }
    } finally {
      _isRefreshing = false;
      notifyListeners();
    }
  }

  void _applyFilter() {
    _items = _filteredItems;
  }
}
