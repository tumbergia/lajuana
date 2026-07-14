import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_icons.dart';

Future<void> showLeadDetailSheet(
  BuildContext context, {
  required LeadItem lead,
  Future<void> Function()? onExport,
  bool pinned = false,
}) {
  final tokens = Theme.of(context).appTokens;
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: false,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(
        top: tokens.radiusXl.topLeft,
      ),
    ),
    builder: (ctx) {
      return _LeadDetailSheetBody(
        lead: lead,
        pinned: pinned,
        onExport: onExport,
      );
    },
  );
}

class _LeadDetailSheetBody extends StatefulWidget {
  const _LeadDetailSheetBody({
    required this.lead,
    required this.pinned,
    this.onExport,
  });

  final LeadItem lead;
  final bool pinned;
  final Future<void> Function()? onExport;

  @override
  State<_LeadDetailSheetBody> createState() => _LeadDetailSheetBodyState();
}

class _LeadDetailSheetBodyState extends State<_LeadDetailSheetBody> {
  bool _exporting = false;

  Future<void> _handleExport() async {
    final export = widget.onExport;
    if (export == null || _exporting) return;
    setState(() => _exporting = true);
    try {
      await export();
      if (!mounted) return;
      Navigator.of(context).pop();
      showAppToast(context, message: 'Indicador exportado');
    } catch (_) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'Error al exportar',
        isError: true,
      );
    } finally {
      if (mounted) setState(() => _exporting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final lead = widget.lead;
    final bottomInset = MediaQuery.viewPaddingOf(context).bottom;

    return SafeArea(
      child: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(
          tokens.spaceXl,
          tokens.spaceLg,
          tokens.spaceXl,
          tokens.spaceXl + bottomInset,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                  borderRadius: tokens.radiusSm,
                ),
              ),
            ),
            SizedBox(height: tokens.spaceXl),
            if (widget.pinned) ...[
              Align(
                alignment: Alignment.centerLeft,
                child: AppBadge(
                  label: 'FIJO',
                  tone: AppBadgeTone.primary,
                  size: AppBadgeSize.sm,
                ),
              ),
              SizedBox(height: tokens.spaceSm),
            ],
            AppMetricCard(
              title: lead.title,
              value: lead.value,
              suffix: lead.unit.isEmpty ? null : lead.unit,
              supportingText: lead.description,
              icon: leadIconFor(lead.icon),
              compact: true,
            ),
            if (lead.details.isNotEmpty) ...[
              SizedBox(height: tokens.spaceXl),
              Text(
                'DESGLOSE',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                    ),
              ),
              SizedBox(height: tokens.spaceSm),
              ...lead.details.map((d) {
                final entries = d.entries.toList();
                return Padding(
                  padding: EdgeInsets.only(bottom: tokens.spaceSm),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          entries.first.value,
                          style:
                              Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                  ),
                        ),
                      ),
                      Text(
                        entries.last.value,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                    ],
                  ),
                );
              }),
            ],
            SizedBox(height: tokens.spaceMd),
            Text(
              'Categoría: ${lead.category}',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
            if (widget.onExport != null) ...[
              SizedBox(height: tokens.spaceXl),
              AppButton(
                label: _exporting ? 'EXPORTANDO…' : 'EXPORTAR',
                icon: Icons.download_rounded,
                variant: AppButtonVariant.secondary,
                expanded: true,
                onPressed: _exporting ? null : _handleExport,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
