import 'dart:async';
import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';
import 'package:mobile_ui/src/voice/voice_context.dart';
import 'package:mobile_ui/src/voice/voice_route.dart';

enum AppNavItem { none, inicio, reservas, equinos, experiencias, mas }

class AppBottomNav extends StatefulWidget {
  final AppNavItem current;
  final ValueChanged<AppNavItem>? onTap;

  const AppBottomNav({super.key, required this.current, this.onTap});

  @override
  State<AppBottomNav> createState() => _AppBottomNavState();
}

class _AppBottomNavState extends State<AppBottomNav>
    with TickerProviderStateMixin {
  static const Duration _holdDelay = Duration(milliseconds: 320);

  AppNavItem? _pressedItem;
  AppNavItem? _voiceLaunchingItem;
  Timer? _holdTimer;

  void _handleTap(AppNavItem item) {
    widget.onTap?.call(item);
  }

  void _onLongPressStart(AppNavItem item) {
    _holdTimer?.cancel();

    setState(() {
      _pressedItem = item;
      _voiceLaunchingItem = null;
    });

    _holdTimer = Timer(_holdDelay, () async {
      if (!mounted || _pressedItem != item) return;

      setState(() {
        _voiceLaunchingItem = item;
      });
      if (!mounted) return;

      final contextVoice = _mapNavToVoice(item);

      await openVoiceScreen(context, voiceContext: contextVoice);

      if (!mounted) return;
      setState(() {
        _pressedItem = null;
        _voiceLaunchingItem = null;
      });
    });
  }

  void _onLongPressEnd() {
    _holdTimer?.cancel();

    if (_voiceLaunchingItem != null) return;

    setState(() {
      _pressedItem = null;
    });
  }

  VoiceContext _mapNavToVoice(AppNavItem item) {
    switch (item) {
      case AppNavItem.inicio:
        return VoiceContext.inicio;
      case AppNavItem.reservas:
        return VoiceContext.reservas;
      case AppNavItem.equinos:
        return VoiceContext.equinos;
      case AppNavItem.experiencias:
        return VoiceContext.experiencias;
      case AppNavItem.mas:
        return VoiceContext.mas;
      case AppNavItem.none:
        return VoiceContext.inicio;
    }
  }

  @override
  void dispose() {
    _holdTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final backgroundColor = isDark
        ? const Color(0xFF131313)
        : theme.colorScheme.surface;

    return Material(
      color: backgroundColor,
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 65,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                Expanded(
                  child: _NavButton(
                    item: AppNavItem.inicio,
                    current: widget.current,
                    label: 'Inicio',
                    icon: Icons.grid_view_rounded,
                    onTap: _handleTap,
                    onHoldStart: _onLongPressStart,
                    onHoldEnd: _onLongPressEnd,
                    pressed: _pressedItem == AppNavItem.inicio,
                    launchingVoice: _voiceLaunchingItem == AppNavItem.inicio,
                  ),
                ),
                Expanded(
                  child: _NavButton(
                    item: AppNavItem.reservas,
                    current: widget.current,
                    label: 'Reservas',
                    icon: Icons.calendar_today_rounded,
                    onTap: _handleTap,
                    onHoldStart: _onLongPressStart,
                    onHoldEnd: _onLongPressEnd,
                    pressed: _pressedItem == AppNavItem.reservas,
                    launchingVoice: _voiceLaunchingItem == AppNavItem.reservas,
                  ),
                ),
                Expanded(
                  child: _NavButton(
                    item: AppNavItem.equinos,
                    current: widget.current,
                    label: 'Equinos',
                    icon: Symbols.chess_knight,
                    onTap: _handleTap,
                    onHoldStart: _onLongPressStart,
                    onHoldEnd: _onLongPressEnd,
                    pressed: _pressedItem == AppNavItem.equinos,
                    launchingVoice: _voiceLaunchingItem == AppNavItem.equinos,
                  ),
                ),
                Expanded(
                  child: _NavButton(
                    item: AppNavItem.experiencias,
                    current: widget.current,
                    label: 'Experiencias',
                    icon: Symbols.explore,
                    onTap: _handleTap,
                    onHoldStart: _onLongPressStart,
                    onHoldEnd: _onLongPressEnd,
                    pressed: _pressedItem == AppNavItem.experiencias,
                    launchingVoice: _voiceLaunchingItem == AppNavItem.experiencias,
                  ),
                ),
                Expanded(
                  child: _NavButton(
                    item: AppNavItem.mas,
                    current: widget.current,
                    label: 'Más',
                    icon: Icons.menu_rounded,
                    onTap: _handleTap,
                    onHoldStart: _onLongPressStart,
                    onHoldEnd: _onLongPressEnd,
                    pressed: _pressedItem == AppNavItem.mas,
                    launchingVoice: _voiceLaunchingItem == AppNavItem.mas,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavButton extends StatelessWidget {
  final AppNavItem item;
  final AppNavItem current;
  final String label;
  final IconData icon;
  final ValueChanged<AppNavItem>? onTap;
  final ValueChanged<AppNavItem>? onHoldStart;
  final VoidCallback? onHoldEnd;
  final bool pressed;
  final bool launchingVoice;

  const _NavButton({
    required this.item,
    required this.current,
    required this.label,
    required this.icon,
    required this.onTap,
    required this.onHoldStart,
    required this.onHoldEnd,
    required this.pressed,
    required this.launchingVoice,
  });

  bool get isActive => item == current;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final voiceMode = pressed || launchingVoice;

    final fg = isActive
        ? (isDark ? const Color(0xFF131313) : theme.colorScheme.onPrimary)
        : (isDark
              ? const Color(0xFFC6C6C6)
              : theme.colorScheme.onSurfaceVariant);

    final bg = isActive
        ? (isDark ? Colors.white : theme.colorScheme.primary)
        : Colors.transparent;

    final double circleScale = launchingVoice ? 1.65 : (pressed ? 1.18 : 1.0);

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onLongPressStart: (_) => onHoldStart?.call(item),
      onLongPressEnd: (_) => onHoldEnd?.call(),
      onLongPressCancel: onHoldEnd,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => onTap?.call(item),
          borderRadius: BorderRadius.circular(isActive && !voiceMode ? 2 : 6),
          splashFactory: NoSplash.splashFactory,
          splashColor: Colors.transparent,
          highlightColor: Colors.transparent,
          hoverColor: Colors.transparent,
          focusColor: Colors.transparent,
          child: Container(
            color: Colors.transparent,
            width: double.infinity,
            height: double.infinity,
            child: Stack(
              alignment: Alignment.center,
              clipBehavior: Clip.none,
              children: [
                AnimatedScale(
                  scale: circleScale,
                  duration: const Duration(milliseconds: 220),
                  curve: Curves.easeOutCubic,
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      final activeWidth = constraints.maxWidth;
                      final targetWidth = voiceMode
                          ? 44.0
                          : (isActive ? activeWidth : 0.0);

                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 180),
                        curve: Curves.easeOutCubic,
                        width: targetWidth,
                        height: voiceMode ? 44 : (isActive ? 48 : 0),
                        decoration: BoxDecoration(
                          color: voiceMode
                              ? (isDark
                                    ? Colors.white
                                    : theme.colorScheme.primary)
                              : bg,
                          borderRadius: BorderRadius.circular(
                            voiceMode ? 999 : (isActive ? 2 : 6),
                          ),
                          boxShadow: voiceMode
                              ? [
                                  BoxShadow(
                                    color:
                                        (isDark
                                                ? Colors.white
                                                : theme.colorScheme.primary)
                                            .withValues(alpha: 0.18),
                                    blurRadius: 18,
                                    spreadRadius: 0,
                                    offset: const Offset(0, 4),
                                  ),
                                ]
                              : null,
                        ),
                      );
                    },
                  ),
                ),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 160),
                      switchInCurve: Curves.easeOut,
                      switchOutCurve: Curves.easeIn,
                      transitionBuilder: (child, animation) {
                        return FadeTransition(
                          opacity: animation,
                          child: ScaleTransition(
                            scale: animation,
                            child: child,
                          ),
                        );
                      },
                      child: Icon(
                        voiceMode ? Icons.mic_rounded : icon,
                        key: ValueKey('${item.name}-$voiceMode'),
                        size: voiceMode ? 20 : 18,
                        color: voiceMode
                            ? (isDark
                                  ? const Color(0xFF131313)
                                  : theme.colorScheme.onPrimary)
                            : fg,
                      ),
                    ),
                    if (!voiceMode) ...[
                      const SizedBox(height: 4),
                      Text(
                        label.toUpperCase(),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontFamily: 'Inter',
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          height: 1.5,
                          letterSpacing: 0.5,
                          color: fg,
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ), // Stack
          ), // Container
        ), // InkWell
      ), // Material
    ); // GestureDetector
  }
}
