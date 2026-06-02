import 'package:flutter/material.dart';

import 'package:mobile_ui/src/theme/theme_extensions.dart';

class AppSelectableCard extends StatelessWidget {
  final Widget child;
  final bool selected;
  final Color? accentColor;
  final VoidCallback? onTap;
  final EdgeInsetsGeometry? padding;
  final BorderRadius? borderRadius;
  final Color? backgroundColor;

  const AppSelectableCard({
    super.key,
    required this.child,
    this.selected = false,
    this.accentColor,
    this.onTap,
    this.padding,
    this.borderRadius,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    final radius = borderRadius ?? tokens.radiusLg;
    final bg =
        backgroundColor ??
        (selected
            ? scheme.surfaceContainerHighest
            : scheme.surfaceContainerLow);

    final content = ClipRRect(
      borderRadius: radius,
      child: Container(
        decoration: BoxDecoration(
          color: bg,
          borderRadius: radius,
          border: selected
              ? Border(
                  bottom: BorderSide(
                    color: accentColor ?? scheme.onSurface,
                    width: 4,
                  ),
                )
              : null,
        ),
        child: Padding(
          padding: padding ?? EdgeInsets.all(tokens.spaceXl),
          child: child,
        ),
      ),
    );

    if (onTap == null) return content;

    return Material(
      color: Colors.transparent,
      borderRadius: radius,
      child: InkWell(borderRadius: radius, onTap: onTap, child: content),
    );
  }
}
