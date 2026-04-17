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
  late final AutoSizeGroup _group;

  @override
  void initState() {
    super.initState();
    _group = AutoSizeGroup();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final children = widget.items.map((item) {
      final selected = item.value == widget.value;
      final theme = Theme.of(context);
      final scheme = theme.colorScheme;

      final child = InkWell(
        borderRadius: BorderRadius.circular(4),
        onTap: () => widget.onChanged(item.value),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          curve: Curves.easeOut,
          height: 36,
          padding: const EdgeInsets.symmetric(horizontal: 12),
          decoration: BoxDecoration(
            color: selected ? scheme.surfaceContainerHighest : Colors.transparent,
            borderRadius: BorderRadius.circular(4),
          ),
          alignment: Alignment.center,
          child: AutoSizeText(
            item.label.toUpperCase(),
            group: _group,
            maxLines: 1,
            minFontSize: 8,
            style: theme.textTheme.labelLarge?.copyWith(
              color: selected ? scheme.onSurface : scheme.onSurfaceVariant,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.35,
            ),
            textAlign: TextAlign.center,
          ),
        ),
      );

      return widget.expanded ? Expanded(child: child) : child;
    }).toList();

    return Container(
      height: 44,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(children: children),
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
