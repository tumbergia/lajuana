import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

/// Full-page / section empty state — mirrors notifications empty rhythm.
class AnalyticsEmptyView extends StatelessWidget {
  const AnalyticsEmptyView({
    super.key,
    required this.title,
    required this.message,
    this.icon = Icons.insights_outlined,
    this.actionLabel,
    this.onAction,
  });

  final String title;
  final String message;
  final IconData icon;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;

    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: tokens.spaceXl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 48, color: scheme.onSurfaceVariant),
            SizedBox(height: tokens.spaceLg),
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            SizedBox(height: tokens.spaceSm),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
            if (actionLabel != null && onAction != null) ...[
              SizedBox(height: tokens.spaceLg),
              AppButton(
                label: actionLabel!,
                icon: Icons.dashboard_customize_rounded,
                variant: AppButtonVariant.secondary,
                onPressed: onAction,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Full-page error — icon + copy + retry, like notifications load failure.
class AnalyticsErrorView extends StatelessWidget {
  const AnalyticsErrorView({
    super.key,
    required this.title,
    required this.message,
    this.onRetry,
  });

  final String title;
  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;

    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: tokens.spaceXl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline_rounded,
              size: 48,
              color: scheme.error,
            ),
            SizedBox(height: tokens.spaceMd),
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: tokens.spaceSm),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
            ),
            if (onRetry != null) ...[
              SizedBox(height: tokens.spaceLg),
              AppButton(
                label: 'Reintentar',
                icon: Icons.refresh_rounded,
                onPressed: onRetry,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Per-module load failure — danger banner with tap-to-retry.
class AnalyticsModuleErrorCard extends StatelessWidget {
  const AnalyticsModuleErrorCard({
    super.key,
    required this.message,
    this.onRetry,
  });

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return AppStatusBanner(
      title: 'No se pudo cargar',
      message: message,
      tone: AppStatusBannerTone.danger,
      icon: Icons.error_outline_rounded,
      badgeLabel: 'Error',
      onTap: onRetry,
    );
  }
}

/// Contrast foreground for a solid domain accent chip.
Color analyticsAccentForeground(Color accent) {
  return ThemeData.estimateBrightnessForColor(accent) == Brightness.dark
      ? Colors.white
      : const Color(0xFF1A1A1A);
}

/// Domain accent + contrasting glyph for category chips.
({Color background, Color foreground}) analyticsDomainChipColors(
  BuildContext context,
  String category,
) {
  final accent = Theme.of(context).analyticsTokens.domainColor(category);
  return (background: accent, foreground: analyticsAccentForeground(accent));
}

/// Small kind label using [AppBadge] or a token-radius chip with domain accent.
class AnalyticsKindBadge extends StatelessWidget {
  const AnalyticsKindBadge({
    super.key,
    required this.label,
    this.filled = false,
    this.accent,
  });

  final String label;
  final bool filled;
  final Color? accent;

  @override
  Widget build(BuildContext context) {
    if (accent == null) {
      return AppBadge(
        label: label,
        tone: AppBadgeTone.primary,
        size: AppBadgeSize.sm,
      );
    }

    final tokens = Theme.of(context).appTokens;
    final bg = filled ? accent! : accent!.withValues(alpha: 0.18);
    final fg = filled ? analyticsAccentForeground(accent!) : accent!;
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: tokens.spaceSm + 2,
        vertical: tokens.spaceXs,
      ),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: tokens.radiusMd,
      ),
      child: Text(
        label.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: fg,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.0,
            ),
      ),
    );
  }
}
