import 'package:flutter/material.dart';

import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';

class LeadCard extends StatelessWidget {
  const LeadCard({
    super.key,
    required this.lead,
    this.onTap,
    this.onExport,
  });

  final LeadItem lead;
  final VoidCallback? onTap;
  final VoidCallback? onExport;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      elevation: 0,
      color: scheme.surfaceContainerLow,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: scheme.outlineVariant, width: 1),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: scheme.primaryContainer,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  _mapIcon(lead.icon),
                  size: 22,
                  color: scheme.onPrimaryContainer,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      lead.title,
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            color: scheme.onSurfaceVariant,
                          ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Text(
                          lead.value,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.w700,
                                color: scheme.onSurface,
                              ),
                        ),
                        if (lead.unit.isNotEmpty) ...[
                          const SizedBox(width: 6),
                          Text(
                            lead.unit,
                            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                  color: scheme.onSurfaceVariant,
                                ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              if (onExport != null)
                IconButton(
                  icon: Icon(Icons.download_rounded, size: 20, color: scheme.onSurfaceVariant),
                  onPressed: onExport,
                  tooltip: 'Exportar',
                ),
              Icon(Icons.chevron_right_rounded, size: 20, color: scheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
    );
  }

  static IconData _mapIcon(String name) {
    switch (name) {
      case 'receipt_long':
        return Icons.receipt_long_rounded;
      case 'pending_actions':
        return Icons.pending_actions_rounded;
      case 'contact_mail':
        return Icons.contact_mail_rounded;
      case 'request_quote':
        return Icons.request_quote_rounded;
      case 'hourglass_bottom':
        return Icons.hourglass_bottom_rounded;
      case 'payments':
        return Icons.payments_rounded;
      case 'check_circle':
        return Icons.check_circle_rounded;
      case 'task_alt':
        return Icons.task_alt_rounded;
      case 'cancel':
        return Icons.cancel_rounded;
      case 'trending_up':
        return Icons.trending_up_rounded;
      case 'account_balance':
        return Icons.account_balance_rounded;
      case 'receipt':
        return Icons.receipt_rounded;
      case 'verified':
        return Icons.verified_rounded;
      case 'groups':
        return Icons.groups_rounded;
      case 'pets':
        return Icons.pets_rounded;
      case 'check':
        return Icons.check_rounded;
      case 'bedtime':
        return Icons.bedtime_rounded;
      case 'construction':
        return Icons.construction_rounded;
      case 'sick':
        return Icons.sick_rounded;
      case 'block':
        return Icons.block_rounded;
      case 'fitness_center':
        return Icons.fitness_center_rounded;
      case 'people':
        return Icons.people_rounded;
      case 'assignment_turned_in':
        return Icons.assignment_turned_in_rounded;
      case 'assignment_late':
        return Icons.assignment_late_rounded;
      case 'percent':
        return Icons.percent_rounded;
      case 'calendar_today':
        return Icons.calendar_today_rounded;
      case 'star':
        return Icons.star_rounded;
      case 'menu_book':
        return Icons.menu_book_rounded;
      case 'public':
        return Icons.public_rounded;
      case 'route':
        return Icons.route_rounded;
      case 'stars':
        return Icons.stars_rounded;
      case 'lock':
        return Icons.lock_rounded;
      case 'emoji_events':
        return Icons.emoji_events_rounded;
      case 'download':
        return Icons.download_rounded;
      case 'hourglass_empty':
        return Icons.hourglass_empty_rounded;
      case 'link':
        return Icons.link_rounded;
      case 'list_alt':
        return Icons.list_alt_rounded;
      case 'flag':
        return Icons.flag_rounded;
      case 'person':
        return Icons.person_rounded;
      case 'group':
        return Icons.group_rounded;
      case 'settings':
        return Icons.settings_rounded;
      case 'bar_chart':
        return Icons.bar_chart_rounded;
      case 'monetization_on':
        return Icons.monetization_on_rounded;
      case 'flag':
        return Icons.flag_rounded;
      case 'pie_chart':
        return Icons.pie_chart_rounded;
      case 'format_list_numbered':
        return Icons.format_list_numbered_rounded;
      default:
        return Icons.help_outline_rounded;
    }
  }
}
