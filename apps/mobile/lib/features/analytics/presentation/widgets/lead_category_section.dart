import 'package:flutter/material.dart';

import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_card.dart';

class LeadCategorySection extends StatefulWidget {
  const LeadCategorySection({
    super.key,
    required this.category,
    this.onLeadTap,
    this.onLeadExport,
  });

  final LeadCategory category;
  final void Function(LeadItem lead)? onLeadTap;
  final void Function(LeadItem lead)? onLeadExport;

  @override
  State<LeadCategorySection> createState() => _LeadCategorySectionState();
}

class _LeadCategorySectionState extends State<LeadCategorySection> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final cat = widget.category;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
            child: Row(
              children: [
                Icon(
                  _mapCategoryIcon(cat.icon),
                  size: 20,
                  color: scheme.primary,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    cat.name,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: scheme.onSurface,
                        ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: scheme.surfaceContainerHigh,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${cat.leads.length}',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                  ),
                ),
                const SizedBox(width: 8),
                Icon(
                  _expanded
                      ? Icons.keyboard_arrow_up_rounded
                      : Icons.keyboard_arrow_down_rounded,
                  size: 20,
                  color: scheme.onSurfaceVariant,
                ),
              ],
            ),
          ),
        ),
        if (_expanded)
          ...cat.leads.map(
            (lead) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: LeadCard(
                lead: lead,
                onTap: widget.onLeadTap != null ? () => widget.onLeadTap!(lead) : null,
                onExport: widget.onLeadExport != null ? () => widget.onLeadExport!(lead) : null,
              ),
            ),
          ),
      ],
    );
  }

  static IconData _mapCategoryIcon(String name) {
    switch (name) {
      case 'bar_chart':
        return Icons.bar_chart_rounded;
      case 'monetization_on':
        return Icons.monetization_on_rounded;
      case 'pets':
        return Icons.pets_rounded;
      case 'people':
        return Icons.people_rounded;
      case 'menu_book':
        return Icons.menu_book_rounded;
      case 'payments':
        return Icons.payments_rounded;
      case 'settings':
        return Icons.settings_rounded;
      case 'public':
        return Icons.public_rounded;
      default:
        return Icons.folder_rounded;
    }
  }
}
