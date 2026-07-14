import 'package:flutter/material.dart';

import 'package:mobile/features/analytics/remote/analytics_api_client.dart';
import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_card.dart';
import 'package:mobile/features/analytics/presentation/screens/all_leads_screen.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';

class LeadsScreen extends StatefulWidget {
  const LeadsScreen({
    super.key,
    required this.analyticsApiClient,
  });

  final AnalyticsApiClient analyticsApiClient;

  @override
  State<LeadsScreen> createState() => _LeadsScreenState();
}

class _LeadsScreenState extends State<LeadsScreen> with RefreshableState {
  late final LeadsController _controller;

  @override
  void initState() {
    super.initState();
    _controller = LeadsController(apiClient: widget.analyticsApiClient);
    _controller.addListener(_onDataChanged);
    _controller.loadLeads();
  }

  @override
  void dispose() {
    _controller.removeListener(_onDataChanged);
    _controller.dispose();
    super.dispose();
  }

  void _onDataChanged() {
    if (mounted) setState(() {});
  }

  @override
  Future<void> onRefresh() => _controller.refresh();

  @override
  Widget build(BuildContext context) {
    final ctrl = _controller;
    final scheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Inicio',
            title: 'Panel de indicadores',
            subtitle: 'Resumen operativo del sistema',
          ),
          const SizedBox(height: 20),
          _buildBody(ctrl, scheme),
        ],
      ),
    );
  }

  Widget _buildBody(LeadsController ctrl, ColorScheme scheme) {
    if (ctrl.isLoading && ctrl.categories.isEmpty) {
      return const AppCenteredLoader();
    }

    if (ctrl.error != null && ctrl.categories.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline_rounded, size: 48, color: scheme.error),
            const SizedBox(height: 12),
            Text(ctrl.error!, style: TextStyle(color: scheme.error)),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => ctrl.loadLeads(forceRefresh: true),
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      );
    }

    final leads = ctrl.randomFive;
    if (leads.isEmpty) {
      return Center(
        child: Text(
          'No hay indicadores disponibles.',
          style: TextStyle(color: scheme.onSurfaceVariant),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Indicadores del momento',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w600,
                color: scheme.onSurface,
              ),
        ),
        const SizedBox(height: 12),
        ListView.separated(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: leads.length + 1,
          separatorBuilder: (_, __) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            if (index == leads.length) {
              return Padding(
                padding: const EdgeInsets.only(top: 8),
                child: OutlinedButton.icon(
                  onPressed: () => _openAllLeads(context),
                  icon: const Icon(Icons.view_list_rounded, size: 18),
                  label: const Text('Ver todos los indicadores'),
                ),
              );
            }
            return LeadCard(lead: leads[index]);
          },
        ),
      ],
    );
  }

  void _openAllLeads(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AllLeadsScreen(controller: _controller),
      ),
    );
  }
}
