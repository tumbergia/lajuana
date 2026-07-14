import 'package:flutter/material.dart';

import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_category_section.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';

class AllLeadsScreen extends StatelessWidget {
  const AllLeadsScreen({
    super.key,
    required this.controller,
  });

  final LeadsController controller;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Todos los indicadores'),
        actions: [
          IconButton(
            icon: const Icon(Icons.download_rounded),
            tooltip: 'Exportar todos',
            onPressed: controller.isLoading ? null : () => controller.exportAll(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Actualizar',
            onPressed: controller.isLoading ? null : () => controller.refresh(),
          ),
        ],
      ),
      body: _buildBody(context, scheme),
    );
  }

  Widget _buildBody(BuildContext context, ColorScheme scheme) {
    if (controller.isLoading && controller.categories.isEmpty) {
      return const AppCenteredLoader();
    }

    if (controller.error != null && controller.categories.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline_rounded, size: 48, color: scheme.error),
            const SizedBox(height: 12),
            Text(controller.error!, style: TextStyle(color: scheme.error)),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => controller.loadLeads(forceRefresh: true),
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      );
    }

    if (controller.categories.isEmpty) {
      return Center(
        child: Text(
          'No hay indicadores disponibles.',
          style: TextStyle(color: scheme.onSurfaceVariant),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
      children: [
        ...controller.categories.map(
          (cat) => LeadCategorySection(
            category: cat,
            onLeadTap: (lead) => _showLeadDetail(context, lead),
            onLeadExport: (lead) => controller.exportSingle(lead.id),
          ),
        ),
      ],
    );
  }

  void _showLeadDetail(BuildContext context, LeadItem lead) {
    final scheme = Theme.of(context).colorScheme;
    showModalBottomSheet(
      context: context,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),
            Text(lead.title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    )),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  lead.value,
                  style: Theme.of(context).textTheme.displaySmall?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: scheme.primary,
                      ),
                ),
                if (lead.unit.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Text(
                      lead.unit,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: scheme.onSurfaceVariant,
                          ),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 12),
            Text(
              lead.description,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
            if (lead.details.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(
                'Desglose',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
              ),
              const SizedBox(height: 8),
              ...lead.details.map((d) {
                final entries = d.entries.toList();
                return Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          entries.first.value,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: scheme.onSurfaceVariant,
                              ),
                        ),
                      ),
                      Text(
                        entries.last.value,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ],
                  ),
                );
              }),
            ],
            const SizedBox(height: 8),
            Text(
              'Categoría: ${lead.category}',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: () {
                Navigator.pop(ctx);
                controller.exportSingle(lead.id);
              },
              icon: const Icon(Icons.download_rounded, size: 18),
              label: const Text('Exportar este indicador'),
            ),
          ],
        ),
      ),
    );
  }
}
