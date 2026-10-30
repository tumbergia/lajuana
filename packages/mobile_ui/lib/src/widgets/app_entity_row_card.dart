import 'package:auto_size_text/auto_size_text.dart';
import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
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
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;
    final Color background = widget.selected
        ? scheme.surfaceContainerHighest
        : scheme.surfaceContainerLow;

    final showAccent = widget.accentColor != null;
    final radius = tokens.radiusLg;
    final titleStyle = theme.textTheme.titleMedium?.copyWith(
      fontWeight: FontWeight.w800,
      color: scheme.onSurface,
      height: 1.2,
      // Long wrapped labels look too airy with tracking; keep spacing for short titles.
      letterSpacing: widget.wrapTitle ? 0 : 0.4,
    );
    final subtitleStyle = theme.textTheme.bodySmall?.copyWith(
      color: scheme.onSurfaceVariant,
      fontWeight: FontWeight.w500,
      height: 1.25,
      letterSpacing: 0.3,
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
      padding: EdgeInsets.all(tokens.spaceLg),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          if (widget.leading != null) ...[
            Align(alignment: Alignment.center, child: widget.leading!),
            SizedBox(width: tokens.spaceMd),
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
                      SizedBox(width: tokens.spaceSm),
                      widget.badge!,
                    ],
                  ],
                ),
                if (widget.subtitle.isNotEmpty) ...[
                  SizedBox(height: tokens.spaceXs),
                  Text(widget.subtitle.toUpperCase(), style: subtitleStyle),
                ],
              ],
            ),
          ),
          if (widget.trailing != null) ...[
            SizedBox(width: tokens.spaceMd),
            Align(alignment: Alignment.center, child: widget.trailing!),
          ],
        ],
      ),
    );

    final content = ClipRRect(
      borderRadius: radius,
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
      borderRadius: radius,
      child: InkWell(borderRadius: radius, onTap: widget.onTap, child: content),
    );
  }
}
