import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';

class AppCenteredBadgeCard extends StatelessWidget {
  const AppCenteredBadgeCard({
    super.key,
    required this.title,
    required this.subtitle,
    this.kicker,
    this.badges = const [],
    this.tone = AppBadgeTone.neutral,
    this.trailingIcon = Icons.edit_rounded,
    this.onTap,
    this.onTrailingTap,
  });

  final String title;
  final String subtitle;
  final String? kicker;
  final List<AppBadge> badges;
  final AppBadgeTone tone;
  final IconData? trailingIcon;
  final VoidCallback? onTap;
  final VoidCallback? onTrailingTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    final borderColor = switch (tone) {
      AppBadgeTone.neutral => scheme.outlineVariant.withValues(alpha: 0.25),
      AppBadgeTone.primary => scheme.primary.withValues(alpha: 0.4),
      AppBadgeTone.success => Colors.green.withValues(alpha: 0.35),
      AppBadgeTone.danger => scheme.error.withValues(alpha: 0.42),
      AppBadgeTone.warning => scheme.tertiary.withValues(alpha: 0.42),
      AppBadgeTone.ghost => scheme.outlineVariant.withValues(alpha: 0.35),
    };

    return Material(
      color: Colors.transparent,
      borderRadius: tokens.radiusLg,
      child: InkWell(
        onTap: onTap,
        borderRadius: tokens.radiusLg,
        child: Container(
          decoration: BoxDecoration(
            color: scheme.surfaceContainerHigh,
            borderRadius: tokens.radiusLg,
            border: Border.all(color: borderColor),
          ),
          child: Stack(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 24, 24, 20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (kicker != null) ...[
                      Text(
                        kicker!.toUpperCase(),
                        textAlign: TextAlign.center,
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.9,
                        ),
                      ),
                      const SizedBox(height: 10),
                    ],
                    Text(
                      title.toUpperCase(),
                      textAlign: TextAlign.center,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.headlineMedium?.copyWith(
                        color: scheme.onSurface,
                        fontWeight: FontWeight.w900,
                        height: 1.02,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      subtitle,
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: scheme.onSurfaceVariant,
                        fontWeight: FontWeight.w600,
                        height: 1.35,
                      ),
                    ),
                    if (badges.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Wrap(
                        alignment: WrapAlignment.center,
                        spacing: 8,
                        runSpacing: 8,
                        children: badges,
                      ),
                    ],
                  ],
                ),
              ),
              if (trailingIcon != null)
                Positioned(
                  right: 4,
                  top: 4,
                  child: IconButton(
                    onPressed: onTrailingTap,
                    icon: Icon(trailingIcon, size: 16),
                    color: scheme.onSurface,
                    tooltip: 'Accion',
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
