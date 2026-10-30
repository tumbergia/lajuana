import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';

enum AppSectionHeaderVariant { hero, compact }

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
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;
    final bool isHero = variant == AppSectionHeaderVariant.hero;

    final TextStyle? titleStyle = isHero
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

    Widget titleBlock() {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (eyebrow != null)
            Padding(
              padding: EdgeInsets.only(
                bottom: isHero ? tokens.spaceSm - 2 : tokens.spaceXs,
              ),
              child: Text(
                eyebrow!.toUpperCase(),
                style: theme.textTheme.labelMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                  fontWeight: FontWeight.w700,
                  letterSpacing: isHero ? 0.7 : 0.5,
                ),
              ),
            ),
          Text(title.toUpperCase(), style: titleStyle),
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
        ],
      );
    }

    return Padding(
      padding: padding ?? EdgeInsets.zero,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final useStackedLayout =
              trailing != null && constraints.maxWidth < 640;

          if (useStackedLayout) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                titleBlock(),
                SizedBox(height: tokens.spaceMd),
                Align(alignment: Alignment.centerLeft, child: trailing!),
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(child: titleBlock()),
              if (trailing != null) ...[
                SizedBox(width: tokens.spaceLg),
                Flexible(
                  fit: FlexFit.loose,
                  child: Align(
                    alignment: Alignment.bottomRight,
                    child: trailing!,
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}
