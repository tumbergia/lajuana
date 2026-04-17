import 'package:flutter/material.dart';
import 'package:auto_size_text/auto_size_text.dart';

class AppSegmentedFilter<T> extends StatefulWidget {
  final List<AppSegmentedFilterItem<T>> items;
  final T value;
  final ValueChanged<T> onChanged;
  final bool expanded;

  const AppSegmentedFilter({
    super.key,
    required this.items,
    required this.value,
    required this.onChanged,
    this.expanded = true,
  });

  @override
  State<AppSegmentedFilter<T>> createState() => _AppSegmentedFilterState<T>();
}

class _AppSegmentedFilterState<T> extends State<AppSegmentedFilter<T>> {
  final AutoSizeGroup _group = AutoSizeGroup();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    final content = Row(
      children: widget.items.map((item) {
        final bool selected = item.value == widget.value;

        final child = InkWell(
          borderRadius: BorderRadius.circular(4),
          onTap: () => widget.onChanged(item.value),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            curve: Curves.easeOut,
            height: 36,
            padding: const EdgeInsets.symmetric(horizontal: 4),
            decoration: BoxDecoration(
              color: selected ? scheme.surfaceContainerHighest : Colors.transparent,
              borderRadius: BorderRadius.circular(4),
            ),
            alignment: Alignment.center,
            child: AutoSizeText(
              item.label.toUpperCase(),
              maxLines: 1,
              minFontSize: 8,
              textAlign: TextAlign.center,
              group: _group,
              style: theme.textTheme.labelLarge?.copyWith(
                color: selected ? scheme.onSurface : scheme.onSurfaceVariant,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.35,
              ),
            ),
          ),
        );

        if (!widget.expanded) return child;
        return Expanded(child: child);
      }).toList(),
    );

    return Container(
      height: 44,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(4),
      ),
      child: content,
    );
  }
}

class AppSegmentedFilterItem<T> {
  final String label;
  final T value;

  const AppSegmentedFilterItem({
    required this.label,
    required this.value,
  });
}
