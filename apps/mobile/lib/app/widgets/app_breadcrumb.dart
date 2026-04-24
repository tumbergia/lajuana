import 'package:flutter/material.dart';

class AppBreadcrumb extends StatelessWidget {
  final List<String> items;
  final String separator;
  final int? currentIndex;
  final ValueChanged<int>? onItemTap;
  final bool uppercase;

  const AppBreadcrumb({
    super.key,
    required this.items,
    this.separator = '>',
    this.currentIndex,
    this.onItemTap,
    this.uppercase = true,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final style = Theme.of(context).textTheme.labelMedium?.copyWith(
      color: scheme.onSurfaceVariant,
      fontWeight: FontWeight.w700,
      letterSpacing: 0.5,
    );

    Widget buildItem(int index, String item) {
      final isCurrent = currentIndex == index;
      final itemStyle = style?.copyWith(
        color: isCurrent ? scheme.onSurface : scheme.onSurfaceVariant,
      );
      final label = Text(
        uppercase ? item.toUpperCase() : item,
        style: itemStyle,
      );
      if (onItemTap == null) return label;

      return Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(4),
          onTap: () => onItemTap?.call(index),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
            child: label,
          ),
        ),
      );
    }

    return Wrap(
      spacing: 6,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        for (int i = 0; i < items.length; i++) ...[
          buildItem(i, items[i]),
          if (i != items.length - 1) Text(separator, style: style),
        ],
      ],
    );
  }
}
