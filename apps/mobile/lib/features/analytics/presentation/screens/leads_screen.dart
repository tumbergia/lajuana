import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/remote/analytics_api_client.dart';
import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_card.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_category_colors.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_detail_sheet.dart';
import 'package:mobile/features/analytics/presentation/screens/all_leads_screen.dart';

class LeadsScreen extends StatefulWidget {
  const LeadsScreen({
    super.key,
    required this.analyticsApiClient,
    this.userDisplayName,
  });

  final AnalyticsApiClient analyticsApiClient;
  final String? userDisplayName;

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

  void _openHub(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AllLeadsScreen(controller: _controller),
      ),
    );
  }

  String get _greetingName {
    final raw = widget.userDisplayName?.trim() ?? '';
    if (raw.isEmpty) return 'equipo';
    return raw.split(RegExp(r'\s+')).first;
  }

  @override
  Widget build(BuildContext context) {
    final ctrl = _controller;
    final tokens = Theme.of(context).appTokens;

    return Padding(
      padding: EdgeInsets.fromLTRB(
        tokens.spaceXl,
        tokens.spaceXl,
        tokens.spaceXl,
        tokens.spaceXl,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Hola',
            title: _greetingName,
          ),
          SizedBox(height: tokens.spaceXl),
          _buildBody(ctrl),
        ],
      ),
    );
  }

  Widget _buildBody(LeadsController ctrl) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;

    if (ctrl.isLoading && ctrl.categories.isEmpty) {
      return const AppCenteredLoader();
    }

    if (ctrl.error != null && ctrl.categories.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline_rounded, size: 48, color: scheme.error),
            SizedBox(height: tokens.spaceMd),
            Text(
              'No se pudieron cargar los indicadores',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: tokens.spaceSm),
            Text(
              ctrl.error!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: tokens.spaceLg),
            AppButton(
              label: 'REINTENTAR',
              icon: Icons.refresh_rounded,
              onPressed: () => ctrl.loadLeads(forceRefresh: true),
            ),
          ],
        ),
      );
    }

    final leads = ctrl.homeLeads;
    if (leads.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.insights_outlined,
              size: 48,
              color: scheme.onSurfaceVariant,
            ),
            SizedBox(height: tokens.spaceMd),
            Text(
              'Sin indicadores',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            SizedBox(height: tokens.spaceSm),
            Text(
              'Abre el panel para ver y configurar indicadores.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: tokens.spaceLg),
            AppButton(
              label: 'VER INDICADORES',
              icon: Icons.view_list_rounded,
              variant: AppButtonVariant.secondary,
              onPressed: () => _openHub(context),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'INDICADORES DEL MOMENTO',
          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w700,
                letterSpacing: 0.8,
                color: scheme.onSurface,
              ),
        ),
        SizedBox(height: tokens.spaceMd),
        ListView.separated(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: leads.length,
          separatorBuilder: (_, _) => SizedBox(height: tokens.spaceSm),
          itemBuilder: (context, index) {
            final lead = leads[index];
            return LeadCard(
              lead: lead,
              pinned: ctrl.isPinned(lead.id),
              accentColor: leadCategoryAccent(context, lead.category),
              onTap: () => showLeadDetailSheet(
                context,
                lead: lead,
                pinned: ctrl.isPinned(lead.id),
                onExport: () => ctrl.exportSingle(lead.id),
              ),
            );
          },
        ),
        SizedBox(height: tokens.spaceLg),
        AppButton(
          label: 'VER Y CONFIGURAR',
          icon: Icons.dashboard_customize_rounded,
          variant: AppButtonVariant.secondary,
          expanded: true,
          onPressed: () => _openHub(context),
        ),
      ],
    );
  }
}
