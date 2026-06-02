import 'package:flutter/foundation.dart';

import '../../domain/repositories/reservations_repository.dart';
import '../../infrastructure/mappers/reservation_mapper.dart';
import '../models/reservation_view_models.dart';
import 'reservations_list_state.dart';

export 'reservations_list_state.dart';

/// Controlador de listado de reservas con filtros, búsqueda y carga real.
///
/// State inmutable via [ReservationsListState]. Getters mantienen API pública
/// idéntica a la versión anterior (W3.7).
class ReservationsListController extends ChangeNotifier {
  ReservationsListController({required ReservationsRepository repository})
      : _repository = repository;

  final ReservationsRepository _repository;
  ReservationsListState _state = const ReservationsListState();

  // ── Getters públicos (API compatible) ──
  ReservationsLoadState get state => _state.loadState;
  List<ReservationRecord> get items => _state.items;
  String get searchQuery => _state.searchQuery;
  String? get filterGroup => _state.filterGroup;
  String? get errorCode => _state.errorCode;
  String? get errorMessage => _state.errorMessage;
  DateTime? get lastSyncAt => _state.lastSyncAt;

  // ── Internal helpers ──

  void _emit(ReservationsListState newState) {
    _state = newState;
    notifyListeners();
  }

  void _applyLocalFilters() {
    var result = _state.allItems;

    // Apply status group filter
    final fg = _state.filterGroup;
    if (fg != null) {
      if (fg == 'eliminadas') {
        result = result.where((item) => item.isDeleted).toList(growable: false);
      } else {
        result = result.where((item) {
          return item.status == fg;
        }).toList(growable: false);
      }
    }

    // Apply search query
    final sq = _state.searchQuery.trim();
    if (sq.isNotEmpty) {
      final q = sq.toLowerCase();
      result = result.where((item) {
        return item.clientName.toLowerCase().contains(q) ||
            item.code.toLowerCase().contains(q) ||
            (item.experienceName?.toLowerCase().contains(q) ?? false);
      }).toList(growable: false);
    }

    _state = _state.copyWith(items: result);
  }

  // ── Public API ──

  /// Carga inicial: primero cache local, luego refresh remoto.
  Future<void> loadInitial() async {
    _emit(_state.copyWith(
      loadState: ReservationsLoadState.loading,
      clearError: true,
    ));

    try {
      final cached = await _repository.getCachedReservations();
      if (cached.isNotEmpty) {
        final records = cached.map((item) => listItemToRecord(item)).toList();
        _state = _state.copyWith(allItems: records);
        _applyLocalFilters();
      }
    } catch (_) {
      // Ignore cache errors during initial load
    }

    try {
      await _fetchFromRemote(isRefresh: false);
    } catch (e) {
      if (_state.allItems.isNotEmpty) {
        _emit(_state.copyWith(
          loadState: ReservationsLoadState.offlineFromCache,
        ));
      } else {
        _emit(_state.copyWith(
          loadState: ReservationsLoadState.error,
          errorCode: 'network.unavailable',
          errorMessage: 'No se pudieron cargar las reservas.',
        ));
      }
    }
  }

  /// Pull-to-refresh.
  Future<void> refresh() async {
    if (_state.loadState == ReservationsLoadState.loading) return;
    _emit(_state.copyWith(
      loadState: ReservationsLoadState.refreshing,
      clearError: true,
    ));

    try {
      await _fetchFromRemote(isRefresh: true);
    } catch (e) {
      if (_state.allItems.isEmpty) {
        _emit(_state.copyWith(loadState: ReservationsLoadState.error));
      } else {
        _emit(_state.copyWith(
          loadState: ReservationsLoadState.offlineFromCache,
        ));
      }
    }
  }

  Future<void> _fetchFromRemote({required bool isRefresh}) async {
    final includeDeleted = _state.filterGroup == 'eliminadas';
    final domainItems = await _repository.listReservations(
      includeDeleted: includeDeleted,
    );
    final now = DateTime.now();

    if (domainItems.isEmpty) {
      _emit(_state.copyWith(
        loadState: ReservationsLoadState.empty,
        items: const [],
        allItems: const [],
        lastSyncAt: now,
      ));
      return;
    }

    final records = domainItems.map((item) => listItemToRecord(item)).toList();
    _state = _state.copyWith(allItems: records, lastSyncAt: now);
    _applyLocalFilters();
    _emit(_state.copyWith(loadState: ReservationsLoadState.success));
  }

  void setFilterGroup(String? group) {
    if (_state.filterGroup == group) return;
    _state = _state.copyWith(filterGroup: group);
    // Cada cambio de filtro requiere re-fetch porque includeDeleted cambia.
    refresh();
  }

  void setSearchQuery(String query) {
    _state = _state.copyWith(searchQuery: query);
    _applyLocalFilters();
    notifyListeners();
  }

  void reset() {
    _emit(const ReservationsListState());
  }
}
