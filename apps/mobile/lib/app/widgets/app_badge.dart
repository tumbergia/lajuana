import 'package:flutter/material.dart';

enum AppBadgeTone {
  neutral,
  primary,
  success,
  danger,
  warning,
  ghost,
}

enum AppBadgeSize {
  sm,
  md,
}

class AppBadge extends StatelessWidget {
  final String label;
  final AppBadgeTone tone;
  final AppBadgeSize size;
  final IconData? icon;
  final bool uppercase;

  const AppBadge({
    super.key,
    required this.label,
    this.tone = AppBadgeTone.neutral,
    this.size = AppBadgeSize.sm,
    this.icon,
    this.uppercase = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    final _BadgeColors colors = switch (tone) {
      AppBadgeTone.neutral => _BadgeColors(
          background: scheme.surfaceContainerHigh,
          foreground: scheme.onSurfaceVariant,
          border: scheme.outlineVariant.withValues(alpha: 0.35),
        ),
      AppBadgeTone.primary => _BadgeColors(
          background: scheme.primary,
          foreground: scheme.onPrimary,
          border: Colors.transparent,
        ),
      AppBadgeTone.success => const _BadgeColors(
          background: Color(0xFF00A431),
          foreground: Colors.white,
          border: Colors.transparent,
        ),
      AppBadgeTone.danger => _BadgeColors(
          background: const Color(0xFF93000A),
          foreground: const Color(0xFFFFDAD6),
          border: Colors.transparent,
        ),
      AppBadgeTone.warning => const _BadgeColors(
          background: Color(0xFF9A6700),
          foreground: Colors.white,
          border: Colors.transparent,
        ),
      AppBadgeTone.ghost => _BadgeColors(
          background: Colors.transparent,
          foreground: scheme.onSurfaceVariant,
          border: scheme.outlineVariant.withValues(alpha: 0.4),
        ),
    };

    final bool isSm = size == AppBadgeSize.sm;
    final EdgeInsets padding = isSm
        ? const EdgeInsets.symmetric(horizontal: 8, vertical: 2)
        : const EdgeInsets.symmetric(horizontal: 10, vertical: 4);

    final TextStyle textStyle = (isSm
            ? theme.textTheme.labelSmall
            : theme.textTheme.labelMedium)
        ?.copyWith(
              color: colors.foreground,
              fontWeight: FontWeight.w700,
              letterSpacing: isSm ? 0.6 : 0.9,
              height: 1.2,
            ) ??
        TextStyle(
          color: colors.foreground,
          fontSize: isSm ? 9 : 10,
          fontWeight: FontWeight.w700,
          letterSpacing: isSm ? 0.6 : 0.9,
        );

    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(2),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: isSm ? 12 : 14, color: colors.foreground),
            const SizedBox(width: 4),
          ],
          Text(
            uppercase ? label.toUpperCase() : label,
            style: textStyle,
          ),
        ],
      ),
    );
  }
}

class _BadgeColors {
  final Color background;
  final Color foreground;
  final Color border;

  const _BadgeColors({
    required this.background,
    required this.foreground,
    required this.border,
  });
}
