import 'package:flutter/material.dart';

import 'app_selectable_card.dart';

class AppStatsCard extends StatelessWidget {
  final String eyebrow;
  final String title;
  final Widget? topRight;
  final List<Widget> children;
  final bool selected;
  final VoidCallback? onTap;

  const AppStatsCard({
    super.key,
    required this.eyebrow,
    required this.title,
    required this.children,
    this.topRight,
    this.selected = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return AppSelectableCard(
      selected: selected,
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            eyebrow.toUpperCase(),
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: scheme.onSurfaceVariant,
              letterSpacing: 0.7,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Text(
                  title.toUpperCase(),
                  style: Theme.of(context).textTheme.displaySmall?.copyWith(
                    color: scheme.onSurface,
                    fontWeight: FontWeight.w800,
                    height: 1.0,
                  ),
                ),
              ),
              if (topRight != null) topRight!,
            ],
          ),
          const SizedBox(height: 20),
          ...children,
        ],
      ),
    );
  }
}