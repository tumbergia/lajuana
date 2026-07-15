import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_card.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_category_colors.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_icons.dart';

class LeadCategorySection extends StatefulWidget {
  const LeadCategorySection({
    super.key,
    required this.category,
    this.onLeadTap,
    this.initiallyExpanded = false,
    this.pinnedIds = const {},
    this.excludedIds = const {},
    this.onTogglePin,
    this.onToggleExcluded,
  });

  final LeadCategory category;
  final void Function(LeadItem lead)? onLeadTap;
  final bool initiallyExpanded;
  final Set<String> pinnedIds;
  final Set<String> excludedIds;
  final void Function(String leadId)? onTogglePin;
  final void Function(String leadId)? onToggleExcluded;

  @override
  State<LeadCategorySection> createState() => _LeadCategorySectionState();
}

class _LeadCategorySectionState extends State<LeadCategorySection> {
  late bool _expanded = widget.initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final cat = widget.category;
    final iconColors = leadCategoryIconColors(context, cat.id);
    final accent = iconColors.background;
    final manage =
        widget.onTogglePin != null || widget.onToggleExcluded != null;
    final radius = tokens.radiusLg;

    // Custom card shell (not AppCard): AppCard's IntrinsicHeight fails inside
    // ListView when sections expand under unbounded height constraints.
    return Padding(
      padding: EdgeInsets.only(bottom: tokens.spaceMd),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: scheme.surfaceContainerLow,
          borderRadius: radius,
          border: Border.all(
            color: scheme.outlineVariant.withValues(alpha: 0.4),
          ),
        ),
        child: ClipRRect(
          borderRadius: radius,
          child: Stack(
            children: [
              Positioned(
                left: 0,
                top: 0,
                bottom: 0,
                width: 4,
                child: ColoredBox(color: accent),
              ),
              Padding(
                padding: const EdgeInsets.only(left: 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Material(
                      color: scheme.surfaceContainer,
                      child: InkWell(
                        onTap: () => setState(() => _expanded = !_expanded),
                        child: Padding(
                          padding: EdgeInsets.symmetric(
                            vertical: tokens.spaceMd,
                            horizontal: tokens.spaceLg,
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 36,
                                height: 36,
                                decoration: BoxDecoration(
                                  color: accent,
                                  borderRadius: tokens.radiusMd,
                                ),
                                child: Icon(
                                  leadIconFor(cat.icon),
                                  size: 18,
                                  color: iconColors.foreground,
                                ),
                              ),
                              SizedBox(width: tokens.spaceMd),
                              Expanded(
                                child: Text(
                                  cat.name.toUpperCase(),
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleSmall
                                      ?.copyWith(
                                        fontWeight: FontWeight.w800,
                                        letterSpacing: 0.6,
                                        color: scheme.onSurface,
                                      ),
                                ),
                              ),
                              AppBadge(
                                label: '${cat.leads.length}',
                                tone: AppBadgeTone.neutral,
                                size: AppBadgeSize.sm,
                                uppercase: false,
                              ),
                              SizedBox(width: tokens.spaceSm),
                              AnimatedRotation(
                                turns: _expanded ? 0.5 : 0,
                                duration: const Duration(milliseconds: 160),
                                curve: Curves.easeOutCubic,
                                child: Icon(
                                  Icons.keyboard_arrow_down_rounded,
                                  size: 22,
                                  color: scheme.onSurfaceVariant,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    if (_expanded)
                      Padding(
                        padding: EdgeInsets.fromLTRB(
                          tokens.spaceMd,
                          tokens.spaceSm,
                          tokens.spaceMd,
                          tokens.spaceMd,
                        ),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            for (final lead in cat.leads)
                              Padding(
                                padding:
                                    EdgeInsets.only(bottom: tokens.spaceSm),
                                child: LeadCard(
                                  lead: lead,
                                  accentColor: accent,
                                  pinned: widget.pinnedIds.contains(lead.id),
                                  excluded:
                                      widget.excludedIds.contains(lead.id),
                                  onTap: widget.onLeadTap != null
                                      ? () => widget.onLeadTap!(lead)
                                      : null,
                                  trailing: manage
                                      ? Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            if (widget.onTogglePin != null)
                                              LeadActionIcon(
                                                icon: widget.pinnedIds
                                                        .contains(lead.id)
                                                    ? Icons.push_pin_rounded
                                                    : Icons.push_pin_outlined,
                                                color: widget.pinnedIds
                                                        .contains(lead.id)
                                                    ? accent
                                                    : scheme.onSurfaceVariant,
                                                tooltip: widget.pinnedIds
                                                        .contains(lead.id)
                                                    ? 'Quitar fijado'
                                                    : 'Fijar en Inicio',
                                                onPressed: () => widget
                                                    .onTogglePin!(lead.id),
                                              ),
                                            if (widget.onToggleExcluded !=
                                                null)
                                              LeadActionIcon(
                                                icon: widget.excludedIds
                                                        .contains(lead.id)
                                                    ? Icons
                                                        .visibility_off_rounded
                                                    : Icons
                                                        .visibility_outlined,
                                                color: widget.excludedIds
                                                        .contains(lead.id)
                                                    ? AppColors.danger
                                                    : scheme.onSurfaceVariant,
                                                tooltip: widget.excludedIds
                                                        .contains(lead.id)
                                                    ? 'Mostrar'
                                                    : 'Ocultar',
                                                onPressed: () =>
                                                    widget.onToggleExcluded!(
                                                  lead.id,
                                                ),
                                              ),
                                          ],
                                        )
                                      : null,
                                ),
                              ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
