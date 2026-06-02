import 'package:flutter/material.dart';

class AppVoiceFab extends StatelessWidget {
  final VoidCallback? onTap;
  final double size;
  final bool elevated;
  final IconData icon;

  const AppVoiceFab({
    super.key,
    this.onTap,
    this.size = 76,
    this.elevated = true,
    this.icon = Icons.mic_rounded,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      elevation: elevated ? 8 : 0,
      shadowColor: Colors.white.withValues(alpha: 0.15),
      borderRadius: BorderRadius.circular(32),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(32),
        child: SizedBox(
          width: size,
          height: size,
          child: Center(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 200),
              transitionBuilder: (child, animation) =>
                  ScaleTransition(scale: animation, child: child),
              child: Icon(
                icon,
                key: ValueKey(icon.codePoint),
                size: 26,
                color: const Color(0xFF1A1C1C),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
