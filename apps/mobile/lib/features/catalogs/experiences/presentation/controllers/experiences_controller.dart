import 'dart:async' show unawaited;

import 'package:flutter/foundation.dart';

import '../../../data/catalogs_repository.dart';
import '../../data/experience_repository.dart';
import '../../domain/experience.dart';

class ExperiencesController extends ChangeNotifier {
  ExperiencesController({
    required ExperienceRepository repository,
    required CatalogsRepository catalogsRepository,
  }) : _repository = repository,
       _catalogsRepository = catalogsRepository;

  final ExperienceRepository _repository;
  final CatalogsRepository _catalogsRepository;

  bool isInitialLoading = false;
  bool isRefreshing = false;
  bool isSyncing = false;
  String? error;
  List<CatalogExperience> items = const <CatalogExperience>[];

  bool get hasLocalData => items.isNotEmpty;

  Future<void> loadLocalThenRefresh({bool refreshServer = true}) async {
    isInitialLoading = true;
    error = null;
    notifyListeners();
    try {
      items = await _repository.list();
    } catch (e) {
      error = e.toString();
    } finally {
      isInitialLoading = false;
      notifyListeners();
    }
    if (refreshServer) {
      unawaited(refreshFromServer());
    }
  }

  Future<void> refreshFromServer() async {
    if (isRefreshing) return;
    isRefreshing = true;
    error = null;
    notifyListeners();
    try {
      await _catalogsRepository.refreshExperiencesFromServer();
      items = await _repository.list();
    } catch (e) {
      error = e.toString();
    } finally {
      isRefreshing = false;
      notifyListeners();
    }
  }

  Future<void> syncNow() async {
    isSyncing = true;
    error = null;
    notifyListeners();
    try {
      await _catalogsRepository.syncNow();
      items = await _repository.list();
    } catch (e) {
      error = e.toString();
    } finally {
      isSyncing = false;
      notifyListeners();
    }
  }

  Future<void> deactivate(String id) async {
    await _repository.deactivate(id);
    await loadLocalThenRefresh(refreshServer: false);
  }
}
