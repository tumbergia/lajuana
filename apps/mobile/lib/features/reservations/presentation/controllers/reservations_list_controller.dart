import 'package:flutter/foundation.dart';

/// Estado de listado de reservas (filtros, paginación incremental).
class ReservationsListController extends ChangeNotifier {
  String _filterValue = 'pendientes';
  int _visibleReservationCount = 4;

  String get filterValue => _filterValue;
  int get visibleReservationCount => _visibleReservationCount;

  void setFilterValue(String value) {
    if (_filterValue == value && _visibleReservationCount == 4) return;
    _filterValue = value;
    _visibleReservationCount = 4;
    notifyListeners();
  }

  void loadMore({int step = 4}) {
    _visibleReservationCount += step;
    notifyListeners();
  }

  void reset() {
    if (_filterValue == 'pendientes' && _visibleReservationCount == 4) return;
    _filterValue = 'pendientes';
    _visibleReservationCount = 4;
    notifyListeners();
  }
}
