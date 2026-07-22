import 'package:flutter/foundation.dart';

import 'package:mobile_domain/src/providers/providers_repository.dart';
import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/providers/infrastructure/mappers/provider_mapper.dart';
import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';

enum ProvidersLoadState {
  idle,
  loading,
  refreshing,
  success,
  empty,
  error,
  offlineFromCache,
}

class ProvidersListController extends ChangeNotifier {
  ProvidersListController({
    required ProvidersRepository repository,
    OutboxRepository? outbox,
  }) : _repository = repository {
    if (outbox != null) {
      _outbox = outbox;
      outbox.addListener(_onOutboxChanged);
    }
  }

  final ProvidersRepository _repository;
  OutboxRepository? _outbox;
  bool _disposed = false;

  ProvidersLoadState state = ProvidersLoadState.idle;
  List<ProviderRecord> items = const <ProviderRecord>[];
  String searchQuery = '';
  bool includeInactive = false;
  String? errorCode;
  String? errorMessage;
  DateTime? lastSyncAt;

  /// Cambios locales pendientes de sincronizar (crear/editar/desactivar).
  bool get hasPendingChanges => (_outbox?.pendingOutboxCount ?? 0) > 0;

  /// Operaciones que fallaron (conflicto/rechazadas).
  bool get hasFailedChanges => (_outbox?.failedOutboxCount ?? 0) > 0;

  List<ProviderRecord> _allItems = const <ProviderRecord>[];

  Future<void> loadInitial() async {
    state = ProvidersLoadState.loading;
    errorCode = null;
    errorMessage = null;
    _notifyListeners();

    try {
      await _fetchFromRemote(isRefresh: false);
    } catch (e) {
      state = ProvidersLoadState.error;
      errorCode = 'network.unavailable';
      errorMessage = 'No se pudieron cargar los proveedores.';
      _notifyListeners();
    }
  }

  Future<void> refresh() async {
    if (state == ProvidersLoadState.loading) return;
    state = ProvidersLoadState.refreshing;
    errorCode = null;
    errorMessage = null;
    _notifyListeners();

    try {
      await _fetchFromRemote(isRefresh: true);
    } catch (e) {
      errorCode = 'network.unavailable';
      errorMessage = 'No se pudo actualizar.';
      if (_allItems.isEmpty) {
        state = ProvidersLoadState.error;
      } else {
        state = ProvidersLoadState.offlineFromCache;
      }
      _notifyListeners();
    }
  }

  Future<void> _fetchFromRemote({required bool isRefresh}) async {
    final domainItems = await _repository.listProviders(includeDeleted: true);
    lastSyncAt = DateTime.now();

    if (domainItems.isEmpty) {
      _allItems = const <ProviderRecord>[];
      items = const <ProviderRecord>[];
      state = ProvidersLoadState.empty;
      _notifyListeners();
      return;
    }

    _allItems = domainItems.map((item) => listItemToRecord(item)).toList();
    _applyLocalFilters();
    state = ProvidersLoadState.success;
    _notifyListeners();
  }

  void setIncludeInactive(bool value) {
    if (includeInactive == value) return;
    includeInactive = value;
    _applyLocalFilters();
    _notifyListeners();
  }

  void setSearchQuery(String query) {
    searchQuery = query;
    _applyLocalFilters();
    _notifyListeners();
  }

  void _applyLocalFilters() {
    var result = _allItems;

    if (includeInactive) {
      result = result
          .where((item) => item.isInactive)
          .toList(growable: false);
    } else {
      result = result
          .where((item) => !item.isInactive)
          .toList(growable: false);
    }

    if (searchQuery.trim().isNotEmpty) {
      final q = searchQuery.toLowerCase().trim();
      result = result
          .where(
            (item) =>
                item.name.toLowerCase().contains(q) ||
                (item.locationLabel?.toLowerCase().contains(q) ?? false) ||
                (item.contactName?.toLowerCase().contains(q) ?? false) ||
                item.typeLabel.toLowerCase().contains(q),
          )
          .toList(growable: false);
    }

    items = result;
  }

  bool get hasAnyRecords => _allItems.isNotEmpty;

  void _onOutboxChanged() {
    // Re-notify so the UI can read hasPendingChanges / hasFailedChanges.
    _notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _outbox?.removeListener(_onOutboxChanged);
    _outbox = null;
    super.dispose();
  }

  void _notifyListeners() {
    if (!_disposed) notifyListeners();
  }

  void reset() {
    includeInactive = false;
    searchQuery = '';
    errorCode = null;
    errorMessage = null;
    state = ProvidersLoadState.idle;
    _notifyListeners();
  }
}
