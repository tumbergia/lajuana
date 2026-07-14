import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:mobile_ui/src/theme/app_theme_notifier.dart';

class AppTopBar extends StatelessWidget implements PreferredSizeWidget {
  static const _bannerAspectRatio = 1600 / 567;
  static const _logoHeight = 40.0;

  final VoidCallback? onNotificationsTap;
  final VoidCallback? onThemeToggleTap;
  final VoidCallback? onOfflineTap;
  final String? title;
  final String logoAssetPath;
  final bool showNotificationDot;

  /// Muestra un ícono compacto de "sin conexión" en vez del banner de estado.
  /// Tocarlo dispara [onOfflineTap] (p. ej. un toast con el detalle).
  final bool showOfflineIndicator;

  const AppTopBar({
    super.key,
    required this.logoAssetPath,
    this.title,
    this.onNotificationsTap,
    this.onThemeToggleTap,
    this.onOfflineTap,
    this.showNotificationDot = false,
    this.showOfflineIndicator = false,
  });

  @override
  Size get preferredSize => const Size.fromHeight(64);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final surfaceColor =
        theme.appBarTheme.backgroundColor ?? const Color(0xFF131313);
    final foregroundColor = theme.appBarTheme.foregroundColor ?? Colors.white;

    // Use provided callback or fall back to AppThemeNotifier
    final effectiveThemeToggle =
        onThemeToggleTap ?? AppThemeNotifier.maybeOf(context)?.onToggle;

    return Material(
      color: surfaceColor,
      child: SafeArea(
        bottom: false,
        child: SizedBox(
          height: 64,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Row(
                    children: [
                      SizedBox(
                        width: _logoHeight * _bannerAspectRatio,
                        height: _logoHeight,
                        child: SvgPicture.asset(
                          logoAssetPath,
                          fit: BoxFit.contain,
                          alignment: Alignment.centerLeft,
                          colorFilter: ColorFilter.mode(
                            foregroundColor,
                            BlendMode.srcIn,
                          ),
                        ),
                      ),
                      if (title != null) ...[
                        const SizedBox(width: 16),
                        Expanded(
                          child: Text(
                            title!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: theme.textTheme.titleLarge?.copyWith(
                              fontFamily: 'Manrope',
                              fontSize: 20,
                              fontWeight: FontWeight.w800,
                              height: 1.4,
                              letterSpacing: 2,
                              color: foregroundColor,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (showOfflineIndicator) ...[
                      _TopBarIconButton(
                        icon: Icons.wifi_off_rounded,
                        onTap: onOfflineTap,
                        showDot: false,
                        iconColor: theme.colorScheme.error,
                        backgroundColor: Colors.transparent,
                      ),
                      const SizedBox(width: 8),
                    ],
                    _TopBarIconButton(
                      icon: theme.brightness == Brightness.dark
                          ? Icons.light_mode_rounded
                          : Icons.dark_mode_rounded,
                      onTap: effectiveThemeToggle,
                      showDot: false,
                      iconColor: foregroundColor,
                      backgroundColor: Colors.transparent,
                    ),
                    const SizedBox(width: 8),
                    _TopBarIconButton(
                      icon: Icons.notifications_none_rounded,
                      onTap: onNotificationsTap,
                      showDot: showNotificationDot,
                      iconColor: foregroundColor,
                      backgroundColor: Colors.transparent,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TopBarIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onTap;
  final bool showDot;
  final Color iconColor;
  final Color backgroundColor;

  const _TopBarIconButton({
    required this.icon,
    required this.onTap,
    required this.showDot,
    required this.iconColor,
    required this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: backgroundColor,
      borderRadius: BorderRadius.circular(4),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(4),
        child: SizedBox(
          width: 32,
          height: 36,
          child: Stack(
            clipBehavior: Clip.none,
            children: [
              const Center(),
              Center(child: Icon(icon, size: 22, color: iconColor)),
              if (showDot)
                const Positioned(right: 3, top: 5, child: _NotificationDot()),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationDot extends StatelessWidget {
  const _NotificationDot();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 7,
      height: 7,
      decoration: BoxDecoration(
        color: Colors.redAccent,
        borderRadius: BorderRadius.circular(999),
      ),
    );
  }
}
