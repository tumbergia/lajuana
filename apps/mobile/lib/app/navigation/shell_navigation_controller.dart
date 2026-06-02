import 'package:flutter/foundation.dart';

import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';

/// Dueño del tab primario del shell: índice actual y notificación a listeners.
class ShellNavigationController extends ChangeNotifier {
  AppNavItem _current = AppNavItem.inicio;

  AppNavItem get currentTab => _current;

  void selectTab(AppNavItem item) {
    if (item == AppNavItem.none) return;
    if (_current == item) return;
    _current = item;
    notifyListeners();
  }
}
