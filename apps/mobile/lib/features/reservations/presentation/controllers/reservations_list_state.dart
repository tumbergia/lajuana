import 'package:mobile/features/reservations/presentation/models/reservation_view_models.dart';

/// Load states for the reservations list.
enum ReservationsLoadState {
  idle,
  loading,
  refreshing,
  success,
  empty,
  error,
  offlineFromCache,
}

/// Immutable state container for [ReservationsListController].
///
/// Using copyWith ensures predictable state transitions and simplifies testing.
class ReservationsListState {
  final ReservationsLoadState loadState;
  final List<ReservationRecord> items;
  final List<ReservationRecord> allItems;
  final String searchQuery;
  final String? filterGroup;
  final String? errorCode;
  final String? errorMessage;
  final DateTime? lastSyncAt;

  const ReservationsListState({
    this.loadState = ReservationsLoadState.idle,
    this.items = const [],
    this.allItems = const [],
    this.searchQuery = '',
    this.filterGroup,
    this.errorCode,
    this.errorMessage,
    this.lastSyncAt,
  });

  ReservationsListState copyWith({
    ReservationsLoadState? loadState,
    List<ReservationRecord>? items,
    List<ReservationRecord>? allItems,
    String? searchQuery,
    String? filterGroup,
    String? errorCode,
    String? errorMessage,
    DateTime? lastSyncAt,
    bool clearError = false,
    bool clearFilterGroup = false,
  }) {
    return ReservationsListState(
      loadState: loadState ?? this.loadState,
      items: items ?? this.items,
      allItems: allItems ?? this.allItems,
      searchQuery: searchQuery ?? this.searchQuery,
      filterGroup: clearFilterGroup ? null : (filterGroup ?? this.filterGroup),
      errorCode: clearError ? null : (errorCode ?? this.errorCode),
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      lastSyncAt: lastSyncAt ?? this.lastSyncAt,
    );
  }
}
