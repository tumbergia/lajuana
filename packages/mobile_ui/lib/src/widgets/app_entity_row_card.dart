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

    final body = Padding(
      padding: EdgeInsets.fromLTRB(16, 16, 16, 16),
      child: Row(
        children: [
          if (widget.leading != null)
            ...[widget.leading!, const SizedBox(width: 12)],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        widget.title.toUpperCase(),
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(
                              fontWeight: FontWeight.w800,
                              color: scheme.onSurface,
                            ),
                      ),
                    ),
                    ?widget.badge,
                    if (widget.badge != null && widget.trailing != null)
                      const SizedBox(width: 8),
                    ?widget.trailing,
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  widget.subtitle.toUpperCase(),
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(
                        color: scheme.onSurfaceVariant,
                        fontWeight: FontWeight.w500,
                      ),
                ),
              ],
            ),
          ),
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
