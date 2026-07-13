import 'package:auto_size_text/auto_size_text.dart';
import 'package:flutter/material.dart';
import 'app_badge.dart';

class AppEntityRowCard extends StatefulWidget {
  final String title;
  final String subtitle;
  final AppBadge? badge;
  final bool selected;
  final VoidCallback? onTap;
  final Color? accentColor;
  final Widget? leading;
  final Widget? trailing;

  /// When true, the title shrinks and/or wraps (up to 2 lines) instead of
  /// ellipsizing. Useful for switch rows and dense settings labels.
  final bool wrapTitle;

  const AppEntityRowCard({
    super.key,
    required this.title,
    required this.subtitle,
    this.badge,
    this.selected = false,
    this.onTap,
    this.accentColor,
    this.leading,
    this.trailing,
    this.wrapTitle = false,
  });

  @override
  State<AppEntityRowCard> createState() => _AppEntityRowCardState();
}

class _AppEntityRowCardState extends State<AppEntityRowCard> {
  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final Color background = widget.selected
        ? scheme.surfaceContainerHighest
        : scheme.surfaceContainerLow;

    final showAccent = widget.accentColor != null;
    final titleStyle = Theme.of(context).textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.w800,
          color: scheme.onSurface,
          height: 1.2,
        );

    final Widget titleText = widget.wrapTitle
        ? AutoSizeText(
            widget.title.toUpperCase(),
            maxLines: 2,
            minFontSize: 12,
            stepGranularity: 0.5,
            overflow: TextOverflow.visible,
            style: titleStyle,
          )
        : Text(
            widget.title.toUpperCase(),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: titleStyle,
          );

    final body = Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (widget.leading != null) ...[
            Align(
              alignment: Alignment.center,
              child: widget.leading!,
            ),
            const SizedBox(width: 12),
          ],
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Expanded(child: titleText),
                    if (widget.badge != null) ...[
                      const SizedBox(width: 8),
                      widget.badge!,
                    ],
                  ],
                ),
                if (widget.subtitle.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    widget.subtitle.toUpperCase(),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                          fontWeight: FontWeight.w500,
                          height: 1.25,
                        ),
                  ),
                ],
              ],
            ),
          ),
          if (widget.trailing != null) ...[
            const SizedBox(width: 12),
            Align(
              alignment: Alignment.center,
              child: widget.trailing!,
            ),
          ],
        ],
      ),
    );

    final content = ClipRRect(
      borderRadius: BorderRadius.circular(4),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 600),
        curve: Curves.easeInOut,
        color: background,
        child: showAccent
            ? Stack(
                children: [
                  body,
                  Positioned(
                    left: 0,
                    top: 0,
                    bottom: 0,
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 600),
                      curve: Curves.easeInOut,
                      width: 4,
                      color: widget.accentColor ?? Colors.transparent,
                    ),
                  ),
                ],
              )
            : body,
      ),
    );

    if (widget.onTap == null) return content;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(4),
        onTap: widget.onTap,
        child: content,
      ),
    );
  }
}
