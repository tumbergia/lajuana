import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';

/// Secondary-screen app bar (pushed routes): back + title + optional actions.
///
/// Matches [AppTopBar] typography and [AppThemeTokens] spacing/radii so pages
/// like Notificaciones / Indicadores don't fall back to Material defaults.
class AppPageAppBar extends StatelessWidget implements PreferredSizeWidget {
  static const double toolbarHeight = 64;

  final String title;
  final List<Widget>? actions;
  final Widget? leading;
  final VoidCallback? onBack;
  final bool automaticallyImplyLeading;

  const AppPageAppBar({
    super.key,
    required this.title,
    this.actions,
    this.leading,
    this.onBack,
    this.automaticallyImplyLeading = true,
  });

  @override
  Size get preferredSize => const Size.fromHeight(toolbarHeight);

  TextStyle _titleStyle(ThemeData theme, Color color) {
    return theme.textTheme.titleLarge?.copyWith(
          fontFamily: 'Manrope',
          fontSize: 20,
          fontWeight: FontWeight.w800,
          height: 1.4,
          letterSpacing: 2,
          color: color,
        ) ??
        TextStyle(
          fontFamily: 'Manrope',
          fontSize: 20,
          fontWeight: FontWeight.w800,
          height: 1.4,
          letterSpacing: 2,
          color: color,
        );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tokens = theme.appTokens;
    final foreground =
        theme.appBarTheme.foregroundColor ?? theme.colorScheme.onSurface;
    final canPop = ModalRoute.of(context)?.canPop ?? false;
    final showBack =
        leading != null ||
        (automaticallyImplyLeading && (onBack != null || canPop));

    // Square back control (36×36) + left inset, so the icon sits centered in
    // its ink square instead of being offset by asymmetric IconButton padding.
    const backSize = 36.0;
    final backLeadingWidth = tokens.spaceXl + backSize;

    return AppBar(
      toolbarHeight: toolbarHeight,
      centerTitle: false,
      elevation: 0,
      scrolledUnderElevation: 0,
      titleSpacing: showBack ? tokens.spaceSm : tokens.spaceXl,
      leadingWidth: showBack ? backLeadingWidth : 0,
      leading:
          leading ??
          (showBack
              ? Padding(
                  padding: EdgeInsets.only(left: tokens.spaceXl),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: SizedBox(
                      width: backSize,
                      height: backSize,
                      child: IconButton(
                        tooltip: MaterialLocalizations.of(
                          context,
                        ).backButtonTooltip,
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints.tightFor(
                          width: backSize,
                          height: backSize,
                        ),
                        style: IconButton.styleFrom(
                          padding: EdgeInsets.zero,
                          minimumSize: const Size(backSize, backSize),
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          shape: RoundedRectangleBorder(
                            borderRadius: tokens.radiusMd,
                          ),
                        ),
                        icon: const Icon(Icons.arrow_back_rounded, size: 22),
                        onPressed:
                            onBack ?? () => Navigator.of(context).maybePop(),
                      ),
                    ),
                  ),
                )
              : null),
      automaticallyImplyLeading: false,
      title: Text(
        title.toUpperCase(),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: _titleStyle(theme, foreground),
      ),
      actionsPadding: EdgeInsets.only(right: tokens.spaceLg),
      actions: actions,
    );
  }
}
