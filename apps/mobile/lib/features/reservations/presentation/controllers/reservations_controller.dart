import 'package:flutter/foundation.dart';

enum ReservationsSubroute {
  resumen,
  participantes,
  pagos,
  asignaciones,
  bitacora,
}

/// Subrutas del módulo Reservas (selector en [ModuleSubrouteHeader]).
class ReservationsController extends ChangeNotifier {
  ReservationsSubroute _subroute = ReservationsSubroute.resumen;

  ReservationsSubroute get subroute => _subroute;

  void selectSubrouteByIndex(int index) {
    final next = ReservationsSubroute.values[index];
    if (_subroute == next) return;
    _subroute = next;
    notifyListeners();
  }

  void reset() {
    if (_subroute == ReservationsSubroute.resumen) return;
    _subroute = ReservationsSubroute.resumen;
    notifyListeners();
  }
}
