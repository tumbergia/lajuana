import 'dart:async' show unawaited;

import 'package:flutter/foundation.dart';

import 'package:mobile/features/catalogs/data/catalogs_repository.dart';
import 'package:mobile/features/catalogs/emergency_contacts/data/emergency_contacts_repository.dart';
import 'package:mobile/features/catalogs/emergency_contacts/domain/emergency_contact.dart';

class EmergencyContactsController extends ChangeNotifier {
  EmergencyContactsController({
    required EmergencyContactsRepository repository,
    required CatalogsRepository catalogsRepository,
  }) : _repository = repository,
       _catalogsRepository = catalogsRepository;

  final EmergencyContactsRepository _repository;
  final CatalogsRepository _catalogsRepository;

  bool isInitialLoading = false;
  bool isRefreshing = false;
  String? error;
  List<CatalogEmergencyContact> items = const <CatalogEmergencyContact>[];

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
      await _catalogsRepository.refreshEmergencyContactsFromServer();
      items = await _repository.list();
    } catch (e) {
      error = e.toString();
    } finally {
      isRefreshing = false;
      notifyListeners();
    }
  }
}
