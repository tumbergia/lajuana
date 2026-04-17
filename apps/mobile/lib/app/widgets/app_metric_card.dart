import 'package:flutter/material.dart';

enum AppMetricCardTone { defaultTone, danger, inverse }

class AppMetricCard extends StatelessWidget {
  final String title;
  final String value;
  final String? suffix;
  final String? supportingText;
  final IconData? icon;
  final AppMetricCardTone tone;
  final bool compact;

  const AppMetricCard({
    super.key,
    required this.title,
    required this.value,
    this.suffix,
    this.supportingText,
    this.icon,
    this.tone = AppMetricCardTone.defaultTone,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final ({
      Color background,
      Color title,
      Color value,
      Color supporting,
      Color icon,
    })
    colors = switch (tone) {
      AppMetricCardTone.defaultTone => (
        background: theme.colorScheme.surfaceContainerHighest,
        title: theme.colorScheme.onSurfaceVariant,
        value: theme.colorScheme.onSurface,
        supporting: theme.colorScheme.onSurfaceVariant,
        icon: theme.colorScheme.onSurfaceVariant,
      ),
      AppMetricCardTone.danger => (
        background: const Color(0xFFBA1A1A), // Light logic error color
        title: Colors.white,
        value: Colors.white,
        supporting: Colors.white,
        icon: Colors.white,
      ),
      AppMetricCardTone.inverse => (
        background: theme.colorScheme.inverseSurface,
        title: theme.colorScheme.onInverseSurface,
        value: theme.colorScheme.onInverseSurface,
        supporting: theme.colorScheme.onInverseSurface.withValues(alpha: 0.8),
        icon: theme.colorScheme.onInverseSurface,
      ),
    };

    return Container(
      padding: EdgeInsets.all(compact ? 20 : 24),
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  title.toUpperCase(),
                  style: theme.textTheme.labelLarge?.copyWith(
                    color: colors.title,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
              if (icon != null) Icon(icon, color: colors.icon, size: 28),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            crossAxisAlignment: WrapCrossAlignment.end,
            spacing: 8,
            runSpacing: 4,
            children: [
              Text(
                value,
                style: theme.textTheme.displayLarge?.copyWith(
                  color: colors.value,
                  fontWeight: FontWeight.w800,
                  fontSize: compact ? 56 : 64,
                  height: 0.95,
                ),
              ),
              if (suffix != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    suffix!,
                    style: theme.textTheme.titleMedium?.copyWith(
                      color: colors.supporting,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
            ],
          ),
          if (supportingText != null) ...[
            const SizedBox(height: 8),
            Text(
              supportingText!,
              style: theme.textTheme.titleMedium?.copyWith(
                color: colors.supporting,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
