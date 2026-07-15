import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/presentation/controllers/dashboard_controller.dart';

/// Catálogo de módulos analíticos disponibles (solo lectura + descripción).
class AnalyticsCatalogScreen extends StatelessWidget {
  const AnalyticsCatalogScreen({super.key, required this.controller});

  final DashboardController controller;

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final catalog = controller.catalog;

    return Scaffold(
      appBar: const AppPageAppBar(title: 'Catálogo de indicadores'),
      body: ListView.separated(
        padding: EdgeInsets.all(tokens.spaceXl),
        itemCount: catalog.length,
        separatorBuilder: (_, __) => SizedBox(height: tokens.spaceSm),
        itemBuilder: (context, index) {
          final mod = catalog[index];
          return AppEntityRowCard(
            title: mod.title,
            subtitle: mod.description,
            badge: mod.blocked
                ? const AppBadge(label: 'No disponible', tone: AppBadgeTone.neutral)
                : null,
          );
        },
      ),
    );
  }
}
