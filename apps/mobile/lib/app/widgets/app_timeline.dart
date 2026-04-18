import 'package:flutter/material.dart';
import 'app_badge.dart';

enum AppTimelineNodeState { active, completed, cancelled, error, neutral }

class AppTimeline extends StatelessWidget {
  final List<Widget> children;
  final double lineLeft;
  final EdgeInsetsGeometry? padding;

  const AppTimeline({
    super.key,
    required this.children,
    this.lineLeft = 12,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: padding ?? EdgeInsets.zero,
      child: Stack(
        children: [
          Positioned(
            left: lineLeft,
            top: 0,
            bottom: 0,
            child: Container(
              width: 1.5,
              color: Theme.of(context).colorScheme.outlineVariant,
            ),
          ),
          Column(children: children),
        ],
      ),
    );
  }
}

class AppTimelineItem extends StatelessWidget {
  final AppTimelineNodeState state;
  final Widget child;
  final double lineLeft;
  final double nodeSize;
  final EdgeInsetsGeometry? margin;

  const AppTimelineItem({
    super.key,
    required this.state,
    required this.child,
    this.lineLeft = 12,
    this.nodeSize = 20,
    this.margin,
  });

  @override
  Widget build(BuildContext context) {
    final bool isDimmed =
        state == AppTimelineNodeState.error ||
        state == AppTimelineNodeState.cancelled;

    Widget content = Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: lineLeft * 2 + nodeSize / 2,
          child: Align(
            alignment: Alignment.topLeft,
            child: Transform.translate(
              offset: Offset(lineLeft - nodeSize / 2, 0),
              child: _TimelineNode(state: state, size: nodeSize),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(child: isDimmed ? Opacity(opacity: 0.5, child: child) : child),
      ],
    );

    return Padding(
      padding: margin ?? const EdgeInsets.only(bottom: 24),
      child: content,
    );
  }
}

class AppTimelineEntryCard extends StatelessWidget {
  final String date;
  final String title;
  final String? description;
  final AppBadge? badge;
  final Widget? highlightedContent;
  final Widget? footer;

  const AppTimelineEntryCard({
    super.key,
    required this.date,
    required this.title,
    this.description,
    this.badge,
    this.highlightedContent,
    this.footer,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  date.toUpperCase(),
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
              ?badge,
            ],
          ),
          const SizedBox(height: 8),
          Text(
            title.toUpperCase(),
            style: theme.textTheme.titleMedium?.copyWith(
              color: scheme.onSurface,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.2,
            ),
          ),
          if (description != null) ...[
            const SizedBox(height: 16),
            Text(
              description!,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: scheme.onSurfaceVariant,
                height: 1.5,
              ),
            ),
          ],
          if (highlightedContent != null) ...[
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerLow,
                borderRadius: BorderRadius.circular(2),
              ),
              child: highlightedContent,
            ),
          ],
          if (footer != null) ...[const SizedBox(height: 16), footer!],
        ],
      ),
    );
  }
}

class AppTimelineMetrics extends StatelessWidget {
  final List<AppTimelineMetricItem> items;

  const AppTimelineMetrics({super.key, required this.items});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Row(
      children: items.map((item) {
        final isLast = item == items.last;
        return Expanded(
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 6),
            decoration: BoxDecoration(
              border: isLast
                  ? null
                  : Border(
                      right: BorderSide(
                        color: scheme.outlineVariant.withValues(alpha: 0.2),
                      ),
                    ),
            ),
            child: Column(
              children: [
                Text(
                  item.value,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: scheme.onSurface,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  item.label.toUpperCase(),
                  textAlign: TextAlign.center,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

class AppTimelineMetricItem {
  final String value;
  final String label;

  const AppTimelineMetricItem({required this.value, required this.label});
}

class _TimelineNode extends StatelessWidget {
  final AppTimelineNodeState state;
  final double size;

  const _TimelineNode({required this.state, required this.size});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    switch (state) {
      case AppTimelineNodeState.active:
        return Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: scheme.onSurface,
            shape: BoxShape.circle,
            border: Border.all(color: scheme.onSurface, width: 2),
          ),
          child: Center(
            child: Container(
              width: size * 0.4,
              height: size * 0.4,
              decoration: BoxDecoration(
                color: scheme.surface,
                shape: BoxShape.circle,
              ),
            ),
          ),
        );
      case AppTimelineNodeState.completed:
        return Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: scheme.surfaceContainerHighest,
            shape: BoxShape.circle,
          ),
          child: Icon(
            Icons.check,
            size: size * 0.6,
            color: scheme.onSurfaceVariant,
          ),
        );
      case AppTimelineNodeState.error:
      case AppTimelineNodeState.cancelled:
        return Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: scheme.error,
            shape: BoxShape.circle,
          ),
          child: Icon(Icons.close, size: size * 0.6, color: scheme.onError),
        );
      case AppTimelineNodeState.neutral:
        return Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: scheme.surfaceContainerHigh,
            shape: BoxShape.circle,
          ),
          child: Icon(
            Icons.remove,
            size: size * 0.6,
            color: scheme.onSurfaceVariant,
          ),
        );
    }
  }
}
