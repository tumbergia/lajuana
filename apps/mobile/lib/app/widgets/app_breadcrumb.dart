import 'package:flutter/material.dart';

class AppBreadcrumb extends StatelessWidget {
  final List<String> items;
  final String separator;

  const AppBreadcrumb({
    super.key,
    required this.items,
    this.separator = '>',
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Wrap(
      spacing: 6,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        for (int i = 0; i < items.length; i++) ...[
          Text(
            items[i].toUpperCase(),
            style: theme.textTheme.labelMedium?.copyWith(
              color: scheme.onSurfaceVariant,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.5,
            ),
          ),
          if (i != items.length - 1)
            Text(
              separator,
              style: theme.textTheme.labelMedium?.copyWith(
                color: scheme.onSurfaceVariant,
                fontWeight: FontWeight.w700,
              ),
            ),
        ],
      ],
    );
  }
}
