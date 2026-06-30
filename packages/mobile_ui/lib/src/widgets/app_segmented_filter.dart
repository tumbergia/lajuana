import 'package:flutter/material.dart';

/// Métricas e interacción compartidas por [AppSegmentedFilter].
abstract final class _AppSegmentedFilterMetrics {
  static const double height = 44;
  static const double padding = 4;
  static const double itemHeight = 36;
  static const double itemHorizontalPadding = 12;
  static const double itemSpacing = 2;
  static const double fadeWidth = 28;
  static const BorderRadius borderRadius = BorderRadius.all(Radius.circular(4));
  static const Duration animationDuration = Duration(milliseconds: 160);

  static Color hoverColor(ColorScheme scheme) =>
      scheme.onSurface.withValues(alpha: 0.06);

  static Color splashColor(ColorScheme scheme) =>
      scheme.onSurface.withValues(alpha: 0.10);

  static Color highlightColor(ColorScheme scheme) =>
      scheme.onSurface.withValues(alpha: 0.04);
}

/// Control segmentado horizontal de ancho completo.
///
/// - Si los labels caben repartidos → ocupa el ancho con columnas iguales.
/// - Si caben pero no alcanzan → se centran con ancho intrínseco.
/// - Si no caben → scroll horizontal breve (sin ellipsis).
///
/// [expanded=false] evita reparto equitativo y centra cuando hay espacio libre.
///
/// Pulsar el segmento ya seleccionado emite [initialValue] (por defecto `null`).
/// Desactiva con [allowDeselect] en tabs de navegación donde siempre debe haber selección.
class AppSegmentedFilter<T> extends StatefulWidget {
  final List<AppSegmentedFilterItem<T>> items;
  final T? value;
  final ValueChanged<T?> onChanged;
  final bool expanded;
  final bool allowDeselect;
  final T? initialValue;

  const AppSegmentedFilter({
    super.key,
    required this.items,
    required this.value,
    required this.onChanged,
    this.expanded = true,
    this.allowDeselect = true,
    this.initialValue,
  });

  @override
  State<AppSegmentedFilter<T>> createState() => _AppSegmentedFilterState<T>();
}

class _AppSegmentedFilterState<T> extends State<AppSegmentedFilter<T>> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollToSelected();
  }

  @override
  void didUpdateWidget(AppSegmentedFilter<T> oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value ||
        oldWidget.items != widget.items ||
        oldWidget.expanded != widget.expanded) {
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

      final position = _scrollController.position;
      if (position.maxScrollExtent <= 0) return;

      final target = (index / widget.items.length) * position.maxScrollExtent -
          position.viewportDimension / 2 +
          (position.viewportDimension / widget.items.length / 2);

      _scrollController.animateTo(
        target.clamp(0.0, position.maxScrollExtent),
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    });
  }

  TextStyle _labelStyle(ThemeData theme, ColorScheme scheme, bool selected) {
    return theme.textTheme.labelLarge!.copyWith(
      color: selected ? scheme.onSurface : scheme.onSurfaceVariant,
      fontWeight: FontWeight.w700,
      letterSpacing: 0.35,
    );
  }

  TextStyle _baseLabelStyle(ThemeData theme) {
    return theme.textTheme.labelLarge!.copyWith(
      fontWeight: FontWeight.w700,
      letterSpacing: 0.35,
    );
  }

  double _measureItemWidth(String label, TextStyle style) {
    final tp = TextPainter(
      text: TextSpan(text: label.toUpperCase(), style: style),
      textDirection: TextDirection.ltr,
      maxLines: 1,
    )..layout();

    return tp.width + (_AppSegmentedFilterMetrics.itemHorizontalPadding * 2);
  }

  double _itemsSpacing() {
    return widget.items.length <= 1
        ? 0
        : _AppSegmentedFilterMetrics.itemSpacing * (widget.items.length - 1);
  }

  (List<double> widths, double totalWidth) _measureItems(ThemeData theme) {
    if (widget.items.isEmpty) return (<double>[], 0);

    final style = _baseLabelStyle(theme);
    final widths = widget.items
        .map((item) => _measureItemWidth(item.label, style))
        .toList(growable: false);

    final totalWidth =
        widths.fold(0.0, (sum, width) => sum + width) + _itemsSpacing();

    return (widths, totalWidth);
  }

  bool _canDistributeEqually(List<double> itemWidths, double maxWidth) {
    if (widget.items.isEmpty || !widget.expanded) return false;

    final perItemWidth = maxWidth / widget.items.length;
    return itemWidths.every((width) => width <= perItemWidth);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return SizedBox(
      width: double.infinity,
      height: _AppSegmentedFilterMetrics.height,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: scheme.surfaceContainerLow,
          borderRadius: _AppSegmentedFilterMetrics.borderRadius,
        ),
        child: ClipRRect(
          borderRadius: _AppSegmentedFilterMetrics.borderRadius,
          child: Material(
            type: MaterialType.transparency,
            color: scheme.surfaceContainerLow,
            clipBehavior: Clip.hardEdge,
            child: Padding(
              padding: const EdgeInsets.all(_AppSegmentedFilterMetrics.padding),
              child: SizedBox(
                height: _AppSegmentedFilterMetrics.itemHeight,
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final innerWidth = constraints.maxWidth;
                    final (itemWidths, totalWidth) = _measureItems(theme);
                    final overflows = totalWidth > innerWidth;

                    if (overflows) {
                      return _buildScrollable(
                        theme,
                        scheme,
                        showFade: true,
                      );
                    }
                    if (_canDistributeEqually(itemWidths, innerWidth)) {
                      return _buildDistributed(theme, scheme);
                    }
                    return _buildCompactCentered(theme, scheme);
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTabItem({
    required ThemeData theme,
    required ColorScheme scheme,
    required AppSegmentedFilterItem<T> item,
    required bool selected,
  }) {
    return AnimatedContainer(
      duration: _AppSegmentedFilterMetrics.animationDuration,
      curve: Curves.easeOut,
      decoration: BoxDecoration(
        color: selected ? scheme.surfaceContainerHighest : Colors.transparent,
        borderRadius: _AppSegmentedFilterMetrics.borderRadius,
      ),
      child: Material(
        type: MaterialType.transparency,
        clipBehavior: Clip.antiAlias,
        borderRadius: _AppSegmentedFilterMetrics.borderRadius,
        child: InkWell(
          borderRadius: _AppSegmentedFilterMetrics.borderRadius,
          hoverColor: _AppSegmentedFilterMetrics.hoverColor(scheme),
          splashColor: _AppSegmentedFilterMetrics.splashColor(scheme),
          highlightColor: _AppSegmentedFilterMetrics.highlightColor(scheme),
          onTap: () {
            if (widget.allowDeselect && selected) {
              widget.onChanged(widget.initialValue);
            } else {
              widget.onChanged(item.value);
            }
          },
          child: SizedBox(
            height: _AppSegmentedFilterMetrics.itemHeight,
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: _AppSegmentedFilterMetrics.itemHorizontalPadding,
              ),
              child: Center(
                child: Text(
                  item.label.toUpperCase(),
                  maxLines: 1,
                  softWrap: false,
                  textAlign: TextAlign.center,
                  style: _labelStyle(theme, scheme, selected),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCompactCentered(ThemeData theme, ColorScheme scheme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        for (int i = 0; i < widget.items.length; i++)
          Padding(
            padding: EdgeInsets.only(
              left: i == 0 ? 0 : _AppSegmentedFilterMetrics.itemSpacing,
            ),
            child: _buildTabItem(
              theme: theme,
              scheme: scheme,
              item: widget.items[i],
              selected: widget.items[i].value == widget.value,
            ),
          ),
      ],
    );
  }

  Widget _buildDistributed(ThemeData theme, ColorScheme scheme) {
    return Row(
      children: [
        for (final item in widget.items)
          Expanded(
            child: _buildTabItem(
              theme: theme,
              scheme: scheme,
              item: item,
              selected: item.value == widget.value,
            ),
          ),
      ],
    );
  }

  Widget _buildScrollable(
    ThemeData theme,
    ColorScheme scheme, {
    required bool showFade,
  }) {
    final children = <Widget>[];
    for (int i = 0; i < widget.items.length; i++) {
      children.add(
        Padding(
          padding: EdgeInsets.only(
            left: i == 0 ? 0 : _AppSegmentedFilterMetrics.itemSpacing,
          ),
          child: _buildTabItem(
            theme: theme,
            scheme: scheme,
            item: widget.items[i],
            selected: widget.items[i].value == widget.value,
          ),
        ),
      );
    }

    return Stack(
      clipBehavior: Clip.hardEdge,
      children: [
        ClipRect(
          child: SingleChildScrollView(
            controller: _scrollController,
            scrollDirection: Axis.horizontal,
            clipBehavior: Clip.hardEdge,
            physics: const BouncingScrollPhysics(
              decelerationRate: ScrollDecelerationRate.fast,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: children,
            ),
          ),
        ),
        if (showFade)
          Positioned(
          right: 0,
          top: 0,
          bottom: 0,
          width: _AppSegmentedFilterMetrics.fadeWidth,
          child: IgnorePointer(
            child: DecoratedBox(
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
