import 'package:flutter/foundation.dart';

enum DashboardSubroute { resumen, pendientes, salidas, sync }

class DashboardController extends ChangeNotifier {
  DashboardSubroute _subroute = DashboardSubroute.resumen;

  DashboardSubroute get subroute => _subroute;

  void selectSubrouteByIndex(int index) {
    final next = DashboardSubroute.values[index];
    if (_subroute == next) return;
    _subroute = next;
    notifyListeners();
  }

  void reset() {
    if (_subroute == DashboardSubroute.resumen) return;
    _subroute = DashboardSubroute.resumen;
    notifyListeners();
  }
}
