import 'package:flutter/foundation.dart';

import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';

/// Dueño del tab primario del shell: índice actual, historial de tabs
/// visitados y notificación a listeners.
class ShellNavigationController extends ChangeNotifier {
  AppNavItem _current = AppNavItem.inicio;

  /// Pila de tabs visitados (más antiguo primero). Permite que el botón
  /// "atrás" regrese al tab anterior en vez de salir de la app.
  final List<AppNavItem> _history = <AppNavItem>[];

  AppNavItem get currentTab => _current;

  /// `true` si hay un tab previo al que regresar con el botón atrás.
  bool get canGoBack => _history.isNotEmpty;

  void selectTab(AppNavItem item) {
    if (item == AppNavItem.none) return;
    if (_current == item) return;
    // Evita duplicados/ciclos: cada tab aparece a lo sumo una vez en el
    // historial, con el más reciente al final.
    _history.remove(item);
    _history.add(_current);
    _current = item;
    notifyListeners();
  }

  /// Regresa al tab visitado anteriormente. Devuelve `false` si no hay
  /// historial (el shell debe entonces aplicar el doble-tap para salir).
  bool goBack() {
    if (_history.isEmpty) return false;
    _current = _history.removeLast();
    notifyListeners();
    return true;
  }
}
