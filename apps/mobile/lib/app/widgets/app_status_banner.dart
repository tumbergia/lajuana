import 'package:flutter/material.dart';

import 'app_badge.dart';
import 'app_card.dart';

enum AppStatusBannerTone { info, warning, danger, success }

class AppStatusBanner extends StatelessWidget {
  const AppStatusBanner({
    super.key,
    required this.title,
    required this.message,
    required this.tone,
    this.icon = Icons.info_outline_rounded,
    this.badgeLabel,
    this.onTap,
  });

  final String title;
  final String message;
  final AppStatusBannerTone tone;
  final IconData icon;
  final String? badgeLabel;
  final VoidCallback? onTap;

  AppBadgeTone _badgeTone() {
    switch (tone) {
      case AppStatusBannerTone.info:
        return AppBadgeTone.primary;
      case AppStatusBannerTone.warning:
        return AppBadgeTone.warning;
      case AppStatusBannerTone.danger:
        return AppBadgeTone.danger;
      case AppStatusBannerTone.success:
        return AppBadgeTone.success;
    }
  }

  Color _accent(ColorScheme scheme) {
    switch (tone) {
      case AppStatusBannerTone.info:
        return scheme.primary;
      case AppStatusBannerTone.warning:
        return scheme.tertiary;
      case AppStatusBannerTone.danger:
        return scheme.error;
      case AppStatusBannerTone.success:
        return scheme.secondary;
    }
  }

  AppCardTone _cardTone() {
    return tone == AppStatusBannerTone.danger
        ? AppCardTone.error
        : AppCardTone.surface;
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final textColor = tone == AppStatusBannerTone.danger
        ? scheme.onErrorContainer
        : scheme.onSurface;
    final supportingColor = tone == AppStatusBannerTone.danger
        ? scheme.onErrorContainer.withValues(alpha: 0.9)
        : scheme.onSurfaceVariant;

    return AppCard(
      tone: _cardTone(),
      accentColor: _accent(scheme),
      outlined: tone != AppStatusBannerTone.danger,
      onTap: onTap,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Icon(icon, size: 18, color: textColor),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title.toUpperCase(),
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: textColor,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.8,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  message,
                  style: Theme.of(
                    context,
                  ).textTheme.bodySmall?.copyWith(color: supportingColor),
                ),
              ],
            ),
          ),
          if (badgeLabel != null) ...[
            const SizedBox(width: 12),
            AppBadge(label: badgeLabel!, tone: _badgeTone(), uppercase: false),
          ],
        ],
      ),
    );
  }
}
