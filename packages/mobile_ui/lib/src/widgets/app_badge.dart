import 'package:flutter/material.dart';

enum AppBadgeTone { neutral, primary, success, danger, warning, ghost }

enum AppBadgeSize { sm, md }

typedef AppBadgeToneColors = ({
  Color background,
  Color foreground,
  Color border,
});

AppBadgeToneColors appBadgeToneColors(BuildContext context, AppBadgeTone tone) {
  final scheme = Theme.of(context).colorScheme;

  return switch (tone) {
    AppBadgeTone.neutral => (
      background: scheme.surfaceContainerHigh,
      foreground: scheme.onSurfaceVariant,
      border: scheme.outlineVariant.withValues(alpha: 0.35),
    ),
    AppBadgeTone.primary => (
      background: scheme.primary,
      foreground: scheme.onPrimary,
      border: Colors.transparent,
    ),
    AppBadgeTone.success => (
      background: const Color(0xFF00A431),
      foreground: Colors.white,
      border: Colors.transparent,
    ),
    AppBadgeTone.danger => (
      background: const Color(0xFFB3261E),
      foreground: Colors.white,
      border: Colors.transparent,
    ),
    AppBadgeTone.warning => (
      background: const Color(0xFF9A6700),
      foreground: Colors.white,
      border: Colors.transparent,
    ),
    AppBadgeTone.ghost => (
      background: Colors.transparent,
      foreground: scheme.onSurfaceVariant,
      border: scheme.outlineVariant.withValues(alpha: 0.4),
    ),
  };
}

Color appBadgeToneTint(
  BuildContext context,
  AppBadgeTone tone, {
  double alpha = 0.22,
}) {
  final colors = appBadgeToneColors(context, tone);
  if (colors.background == Colors.transparent) {
    return Theme.of(context).colorScheme.surfaceContainerLow;
  }
  return colors.background.withValues(alpha: alpha);
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
    final colors = appBadgeToneColors(context, tone);

    final bool isSm = size == AppBadgeSize.sm;
    final EdgeInsets padding = isSm
        ? const EdgeInsets.symmetric(horizontal: 8, vertical: 2)
        : const EdgeInsets.symmetric(horizontal: 10, vertical: 4);

    final TextStyle style =
        (isSm ? theme.textTheme.labelSmall : theme.textTheme.labelMedium)
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
          Text(uppercase ? label.toUpperCase() : label, style: style),
        ],
      ),
    );
  }
}
