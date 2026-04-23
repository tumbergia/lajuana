import 'package:flutter/foundation.dart';

enum EquinesSubroute { resumen, historial, disponibilidad, cuidado }

class EquinesController extends ChangeNotifier {
  EquinesSubroute _subroute = EquinesSubroute.resumen;

  EquinesSubroute get subroute => _subroute;

  void selectSubrouteByIndex(int index) {
    final next = EquinesSubroute.values[index];
    if (_subroute == next) return;
    _subroute = next;
    notifyListeners();
  }

  void reset() {
    if (_subroute == EquinesSubroute.resumen) return;
    _subroute = EquinesSubroute.resumen;
    notifyListeners();
  }
}
