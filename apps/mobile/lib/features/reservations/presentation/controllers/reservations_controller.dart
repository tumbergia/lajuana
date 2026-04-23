import 'package:flutter/foundation.dart';

enum ReservationsSubroute {
  resumen,
  participantes,
  pagos,
  asignaciones,
  bitacora,
}

class ReservationsController extends ChangeNotifier {
  ReservationsSubroute _subroute = ReservationsSubroute.resumen;
  String _filterValue = 'pendientes';
  int _visibleReservationCount = 4;

  ReservationsSubroute get subroute => _subroute;
  String get filterValue => _filterValue;
  int get visibleReservationCount => _visibleReservationCount;

  void selectSubrouteByIndex(int index) {
    final next = ReservationsSubroute.values[index];
    if (_subroute == next) return;
    _subroute = next;
    notifyListeners();
  }

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
    final shouldReset =
        _subroute != ReservationsSubroute.resumen ||
        _filterValue != 'pendientes' ||
        _visibleReservationCount != 4;
    if (!shouldReset) return;

    _subroute = ReservationsSubroute.resumen;
    _filterValue = 'pendientes';
    _visibleReservationCount = 4;
    notifyListeners();
  }
}
