import 'package:flutter/material.dart';
import '../theme/theme_extensions.dart';

enum AppSectionHeaderVariant {
  hero,
  compact,
}

class AppSectionHeader extends StatelessWidget {
  final String title;
  final String? eyebrow;
  final String? subtitle;
  final Widget? trailing;
  final AppSectionHeaderVariant variant;
  final EdgeInsetsGeometry? padding;

  const AppSectionHeader({
    super.key,
    required this.title,
    this.eyebrow,
    this.subtitle,
    this.trailing,
    this.variant = AppSectionHeaderVariant.hero,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tokens = theme.appTokens;
    final scheme = theme.colorScheme;

    final bool hero = variant == AppSectionHeaderVariant.hero;

    final titleStyle = hero
        ? theme.textTheme.displaySmall?.copyWith(
            fontWeight: FontWeight.w800,
            height: 1.0,
            letterSpacing: -0.9,
          )
        : theme.textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w800,
            height: 1.1,
            letterSpacing: -0.4,
          );

    return Padding(
      padding: padding ?? EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (eyebrow != null)
            Padding(
              padding: EdgeInsets.only(bottom: hero ? 6 : 4),
              child: Text(
                eyebrow!.toUpperCase(),
                style: theme.textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                  fontWeight: FontWeight.w700,
                  letterSpacing: hero ? 0.7 : 0.5,
                ),
              ),
            ),
          Text(
            title.toUpperCase(),
            style: titleStyle,
          ),
          if (subtitle != null)
            Padding(
              padding: EdgeInsets.only(top: tokens.spaceSm),
              child: Text(
                subtitle!,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
            ),
          if (trailing != null)
            Padding(
              padding: EdgeInsets.only(top: tokens.spaceLg),
              child: trailing!,
            ),
        ],
      ),
    );
  }
}
