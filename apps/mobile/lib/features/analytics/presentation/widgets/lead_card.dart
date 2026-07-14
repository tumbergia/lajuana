import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

import 'package:mobile/features/analytics/presentation/controllers/leads_controller.dart';
import 'package:mobile/features/analytics/presentation/widgets/lead_icons.dart';

class LeadCard extends StatelessWidget {
  const LeadCard({
    super.key,
    required this.lead,
    this.onTap,
    this.pinned = false,
    this.excluded = false,
    this.accentColor,
    this.trailing,
  });

  final LeadItem lead;
  final VoidCallback? onTap;
  final bool pinned;
  final bool excluded;
  final Color? accentColor;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    final chipBg = excluded
        ? AppColors.danger
        : (accentColor ?? scheme.primary);
    final iconFg =
        ThemeData.estimateBrightnessForColor(chipBg) == Brightness.dark
            ? Colors.white
            : const Color(0xFF1A1A1A);
    final valueLabel =
        lead.unit.isEmpty ? lead.value : '${lead.value} ${lead.unit}';

    AppBadge? badge;
    if (pinned) {
      badge = const AppBadge(
        label: 'FIJO',
        tone: AppBadgeTone.primary,
        size: AppBadgeSize.sm,
      );
    } else if (excluded) {
      badge = const AppBadge(
        label: 'OCULTO',
        tone: AppBadgeTone.danger,
        size: AppBadgeSize.sm,
      );
    }

    return AppEntityRowCard(
      title: valueLabel,
      subtitle: lead.title,
      onTap: onTap,
      wrapTitle: true,
      accentColor: excluded ? AppColors.danger : null,
      badge: badge,
      leading: Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: chipBg,
          borderRadius: tokens.radiusMd,
        ),
        child: Icon(
          leadIconFor(lead.icon),
          size: 22,
          color: iconFg,
        ),
      ),
      trailing: trailing ??
          Icon(
            Icons.chevron_right_rounded,
            size: 20,
            color: scheme.onSurfaceVariant,
          ),
    );
  }
}

/// Compact action icon that won't blow AppEntityRowCard trailing layout.
class LeadActionIcon extends StatelessWidget {
  const LeadActionIcon({
    super.key,
    required this.icon,
    required this.onPressed,
    this.color,
    this.tooltip,
  });

  final IconData icon;
  final VoidCallback onPressed;
  final Color? color;
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final child = Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        customBorder: const CircleBorder(),
        child: SizedBox(
          width: 36,
          height: 36,
          child: Icon(
            icon,
            size: 20,
            color: color ?? scheme.onSurfaceVariant,
          ),
        ),
      ),
    );
    if (tooltip == null) return child;
    return Tooltip(message: tooltip!, child: child);
  }
}
