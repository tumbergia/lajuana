import 'package:flutter/foundation.dart';

enum ParticipantsSubroute { resumen, participantes, historial }

class ParticipantsController extends ChangeNotifier {
  ParticipantsSubroute _subroute = ParticipantsSubroute.resumen;

  ParticipantsSubroute get subroute => _subroute;

  void selectSubrouteByIndex(int index) {
    final next = ParticipantsSubroute.values[index];
    if (_subroute == next) return;
    _subroute = next;
    notifyListeners();
  }

  void reset() {
    if (_subroute == ParticipantsSubroute.resumen) return;
    _subroute = ParticipantsSubroute.resumen;
    notifyListeners();
  }
}
