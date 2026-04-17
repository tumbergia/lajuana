import 'package:flutter/material.dart';
enum AppMetricCardTone {
  defaultTone,
  danger,
  inverse,
}

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
    final scheme = theme.colorScheme;

    final _MetricToneColors colors = switch (tone) {
      AppMetricCardTone.defaultTone => _MetricToneColors(
          background: scheme.surfaceContainerHighest,
          title: scheme.onSurfaceVariant,
          value: scheme.onSurface,
          supporting: scheme.onSurfaceVariant,
          icon: scheme.onSurfaceVariant,
        ),
      AppMetricCardTone.danger => const _MetricToneColors(
          background: Color(0xFFB00008),
          title: Color(0xFFFFDAD6),
          value: Colors.white,
          supporting: Color(0xFFFFDAD6),
          icon: Color(0xFFFFDAD6),
        ),
      AppMetricCardTone.inverse => const _MetricToneColors(
          background: Colors.white,
          title: Color(0xFF1A1C1C),
          value: Color(0xFF1A1C1C),
          supporting: Color(0xFF3A3C3C),
          icon: Color(0xFF1A1C1C),
        ),
    };

    final EdgeInsets padding = compact
        ? const EdgeInsets.all(20)
        : const EdgeInsets.all(24);

    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(8),
      ),
      child: DefaultTextStyle(
        style: theme.textTheme.bodyMedium ?? const TextStyle(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
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
                if (icon != null)
                  Icon(
                    icon,
                    color: colors.icon,
                    size: 28,
                  ),
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
      ),
    );
  }
}

class _MetricToneColors {
  final Color background;
  final Color title;
  final Color value;
  final Color supporting;
  final Color icon;

  const _MetricToneColors({
    required this.background,
    required this.title,
    required this.value,
    required this.supporting,
    required this.icon,
  });
}
