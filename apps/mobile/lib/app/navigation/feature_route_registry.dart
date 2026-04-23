import 'package:flutter/widgets.dart';

import '../widgets/app_bottom_nav.dart';

/// Registro declarativo tab → raíz del Navigator anidado (sin lógica de negocio).
typedef FeatureRootBuilder = Widget Function(BuildContext context);

class FeatureRouteRegistry {
  const FeatureRouteRegistry({
    required this.builders,
  });

  final Map<AppNavItem, FeatureRootBuilder> builders;

  Widget buildRoot(BuildContext context, AppNavItem tab) {
    final builder = builders[tab];
    if (builder == null) {
      return const SizedBox.shrink();
    }
    return builder(context);
  }
}
