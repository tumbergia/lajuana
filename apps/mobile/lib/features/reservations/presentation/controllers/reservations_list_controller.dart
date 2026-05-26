import 'package:flutter/foundation.dart';

import '../../domain/repositories/reservations_repository.dart';
import '../../infrastructure/mappers/reservation_mapper.dart';
import '../models/reservation_view_models.dart';

enum ReservationsLoadState {
  idle,
  loading,
  refreshing,
  success,
  empty,
  error,
  offlineFromCache,
}

/// Controlador de listado de reservas con filtros, búsqueda y carga real.
class ReservationsListController extends ChangeNotifier {
  ReservationsListController({required ReservationsRepository repository})
      : _repository = repository;

  final ReservationsRepository _repository;

  ReservationsLoadState state = ReservationsLoadState.idle;
  List<ReservationRecord> items = const <ReservationRecord>[];
  String searchQuery = '';
  String? filterGroup; // "pendientes" | "confirmadas" | "cerradas"
  String? errorCode;
  String? errorMessage;
  DateTime? lastSyncAt;

  // Full unfiltered list kept for local filtering.
  List<ReservationRecord> _allItems = const <ReservationRecord>[];

  /// Carga inicial: primero cache local, luego refresh remoto.
  Future<void> loadInitial() async {
    state = ReservationsLoadState.loading;
    errorCode = null;
    errorMessage = null;
    notifyListeners();

    try {
      final cached = await _repository.getCachedReservations();
      if (cached.isNotEmpty) {
        _allItems = cached.map((item) => listItemToRecord(item)).toList();
        _applyLocalFilters();
      }
    } catch (_) {
      // Ignore cache errors during initial load
    }

    try {
      await _fetchFromRemote(isRefresh: false);
    } catch (e) {
      if (_allItems.isNotEmpty) {
        state = ReservationsLoadState.offlineFromCache;
      } else {
        state = ReservationsLoadState.error;
        errorCode = 'network.unavailable';
        errorMessage = 'No se pudieron cargar las reservas.';
      }
      notifyListeners();
    }
  }

  /// Pull-to-refresh.
  Future<void> refresh() async {
    if (state == ReservationsLoadState.loading) return;
    state = ReservationsLoadState.refreshing;
    errorCode = null;
    errorMessage = null;
    notifyListeners();

    try {
      await _fetchFromRemote(isRefresh: true);
    } catch (e) {
      errorCode = 'network.unavailable';
      errorMessage = 'No se pudo actualizar.';
      if (_allItems.isEmpty) {
        state = ReservationsLoadState.error;
      } else {
        state = ReservationsLoadState.offlineFromCache;
      }
      notifyListeners();
    }
  }

  Future<void> _fetchFromRemote({required bool isRefresh}) async {
    final domainItems = await _repository.listReservations();
    lastSyncAt = DateTime.now();

    if (domainItems.isEmpty) {
      _allItems = const <ReservationRecord>[];
      items = const <ReservationRecord>[];
      state = ReservationsLoadState.empty;
      notifyListeners();
      return;
    }

    _allItems = domainItems.map((item) => listItemToRecord(item)).toList();
    _applyLocalFilters();
    state = ReservationsLoadState.success;
    notifyListeners();
  }

  void setFilterGroup(String? group) {
    if (filterGroup == group) return;
    filterGroup = group;
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

    // Apply status group filter
    if (filterGroup != null) {
      result = result.where((item) {
        return item.status == filterGroup;
      }).toList(growable: false);
    }

    // Apply search query
    if (searchQuery.trim().isNotEmpty) {
      final q = searchQuery.toLowerCase().trim();
      result = result.where((item) {
        return item.clientName.toLowerCase().contains(q) ||
            item.code.toLowerCase().contains(q) ||
            (item.experienceName?.toLowerCase().contains(q) ?? false);
      }).toList(growable: false);
    }

    items = result;
  }

  void reset() {
    filterGroup = null;
    searchQuery = '';
    errorCode = null;
    errorMessage = null;
    state = ReservationsLoadState.idle;
    notifyListeners();
  }
}
