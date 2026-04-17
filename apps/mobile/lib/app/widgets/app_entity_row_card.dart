import 'package:flutter/material.dart';
import 'app_badge.dart';

class AppEntityRowCard extends StatelessWidget {
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
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final Color background =
        selected ? scheme.surfaceContainerHighest : scheme.surfaceContainerLow;

    final content = Container(
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          if (selected)
            Container(
              width: 4,
              height: 69,
              decoration: BoxDecoration(
                color: accentColor ?? scheme.onSurface,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(4),
                  bottomLeft: Radius.circular(4),
                ),
              ),
            ),
          Expanded(
            child: Padding(
              padding: EdgeInsets.fromLTRB(
                selected ? 12 : 16,
                16,
                16,
                16,
              ),
              child: Row(
                children: [
                  if (leading != null) ...[
                    leading!,
                    const SizedBox(width: 12),
                  ],
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                title.toUpperCase(),
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(
                                      fontWeight: FontWeight.w800,
                                      color: scheme.onSurface,
                                    ),
                              ),
                            ),
                            if (badge != null) badge!,
                            if (trailing != null) trailing!,
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          subtitle.toUpperCase(),
                          style:
                              Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                    fontWeight: FontWeight.w500,
                                  ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );

    if (onTap == null) return content;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(4),
        onTap: onTap,
        child: content,
      ),
    );
  }
}
