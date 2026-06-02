import 'package:flutter/material.dart';
import 'package:auto_size_text/auto_size_text.dart';

/// Control segmentado horizontal.
///
/// Se adapta al contenido automáticamente:
/// - Si los items caben sin desbordar → distribuye equitativamente (Row + Expanded).
/// - Si desbordan o [expanded=false] → modo scroll horizontal con ancho intrínseco,
///   fade de desbordamiento y auto-scroll al item seleccionado.
///
/// Usar [expanded=true] (default) para 2–4 items con etiquetas cortas.
/// [expanded=false] fuerza el modo scroll, útil para 5+ items o etiquetas largas.
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
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _group = AutoSizeGroup();
    _scrollToSelected();
  }

  @override
  void didUpdateWidget(AppSegmentedFilter<T> oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _scrollToSelected();
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToSelected() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      final index = widget.items.indexWhere(
        (item) => item.value == widget.value,
      );
      if (index < 0) return;

      // Calculate approximate offset to center the selected item.
      final totalExtent = _scrollController.position.maxScrollExtent;
      if (totalExtent <= 0) return;
      final target = (index / widget.items.length) * totalExtent -
          _scrollController.position.viewportDimension / 2 +
          (_scrollController.position.viewportDimension / widget.items.length /
              2);

      _scrollController.animateTo(
        target.clamp(0.0, totalExtent),
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Container(
      height: 44,
      padding: const EdgeInsets.all(4),
      clipBehavior: Clip.hardEdge,
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: const BorderRadius.all(Radius.circular(4)),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          // 8 = container padding (4 each side)
          final overflow = _measureOverflow(theme, constraints.maxWidth - 8);
          final useScroll = overflow || !widget.expanded;

          if (useScroll) {
            return _buildScrollable(theme, scheme, overflow);
          }
          return _buildExpanded(theme, scheme);
        },
      ),
    );
  }

  bool _measureOverflow(ThemeData theme, double maxWidth) {
    // maxWidth = constraints.maxWidth - 8 (container padding already descontado)
    if (widget.items.isEmpty) return false;

    final textStyle = theme.textTheme.labelLarge?.copyWith(
      letterSpacing: 0.35,
      fontWeight: FontWeight.w700,
    );

    final int itemCount = widget.items.length;
    // Row reparte maxWidth equitativamente entre los Expanded.
    final double perItemWidth = maxWidth / itemCount;

    double totalWidth = 0;

    for (final item in widget.items) {
      final tp = TextPainter(
        text: TextSpan(
          text: item.label.toUpperCase(),
          style: textStyle,
        ),
        textDirection: TextDirection.ltr,
      )..layout();

      final double textWidth = tp.width;
      // ancho intrínseco del item completo (texto + padding lateral)
      final double itemWidth = textWidth + 24;

      // Si un solo item es más ancho que su porción equitativa en expanded
      // mode, el label se comprime/desborda → modo scroll.
      if (itemWidth > perItemWidth) return true;

      totalWidth += itemWidth;
    }

    // Si el ancho total intrínseco supera el disponible → modo scroll.
    return totalWidth > maxWidth;
  }

  Widget _buildExpanded(ThemeData theme, ColorScheme scheme) {
    final children = widget.items.map((item) {
      final selected = item.value == widget.value;

      return Expanded(
        child: InkWell(
          borderRadius: const BorderRadius.all(Radius.circular(4)),
          onTap: () => widget.onChanged(item.value),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            curve: Curves.easeOut,
            height: 36,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: selected
                  ? scheme.surfaceContainerHighest
                  : Colors.transparent,
              borderRadius: const BorderRadius.all(Radius.circular(4)),
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
        ),
      );
    }).toList();

    return Row(children: children);
  }

  Widget _buildScrollable(
    ThemeData theme,
    ColorScheme scheme,
    bool overflow,
  ) {
    final children = <Widget>[];
    for (int i = 0; i < widget.items.length; i++) {
      final item = widget.items[i];
      final selected = item.value == widget.value;

      children.add(
        Container(
          margin: EdgeInsets.only(
            left: i == 0 ? 0 : 2,
            right: i == widget.items.length - 1 ? 0 : 2,
          ),
          child: InkWell(
            borderRadius: const BorderRadius.all(Radius.circular(4)),
            onTap: () => widget.onChanged(item.value),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 160),
              curve: Curves.easeOut,
              height: 36,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: selected
                    ? scheme.surfaceContainerHighest
                    : Colors.transparent,
                borderRadius: const BorderRadius.all(Radius.circular(4)),
              ),
              alignment: Alignment.center,
              child: Text(
                item.label.toUpperCase(),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.labelLarge?.copyWith(
                  color: selected ? scheme.onSurface : scheme.onSurfaceVariant,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.35,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ),
      );
    }

    return Stack(
      children: [
        SingleChildScrollView(
          controller: _scrollController,
          scrollDirection: Axis.horizontal,
          physics: const BouncingScrollPhysics(),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: children,
          ),
        ),
        // Fade de desbordamiento derecho — solo visible si hay overflow
        if (overflow)
          Positioned(
            right: 0,
            top: 0,
            bottom: 0,
            width: 28,
            child: IgnorePointer(
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.centerRight,
                    end: Alignment.centerLeft,
                    colors: [
                      scheme.surfaceContainerLow,
                      scheme.surfaceContainerLow.withValues(alpha: 0.0),
                    ],
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class AppSegmentedFilterItem<T> {
  final String label;
  final T value;

  const AppSegmentedFilterItem({required this.label, required this.value});
}
