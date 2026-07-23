import 'package:flutter/foundation.dart';

import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';

/// Dueño del tab primario del shell: índice actual, historial de tabs
/// visitados y notificación a listeners.
class ShellNavigationController extends ChangeNotifier {
  ShellNavigationController({AppNavItem initialTab = AppNavItem.inicio})
    : _current = initialTab;

  AppNavItem _current;

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

  /// Fija el tab activo sin historial (p. ej. al cambiar de rol).
  void resetTo(AppNavItem item) {
    if (item == AppNavItem.none) return;
    _history.clear();
    if (_current == item) {
      notifyListeners();
      return;
    }
    _current = item;
    notifyListeners();
  }

  /// Si el tab actual no está en [allowed], salta a [fallback].
  void ensureAllowed(Iterable<AppNavItem> allowed, AppNavItem fallback) {
    final allowedSet = allowed.toSet();
    if (allowedSet.contains(_current)) return;
    resetTo(fallback);
  }

  /// Regresa al tab visitado anteriormente, saltando tabs no permitidos.
  /// Devuelve `false` si no hay historial usable.
  bool goBack({Iterable<AppNavItem>? allowed}) {
    final allowedSet = allowed?.toSet();
    while (_history.isNotEmpty) {
      final previous = _history.removeLast();
      if (allowedSet != null && !allowedSet.contains(previous)) {
        continue;
      }
      _current = previous;
      notifyListeners();
      return true;
    }
    return false;
  }
}
