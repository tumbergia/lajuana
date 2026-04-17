import 'dart:ui';
import 'package:flutter/material.dart';

enum AppNavItem {
  inicio,
  reservas,
  equinos,
  clientes,
  mas,
}

class AppBottomNav extends StatelessWidget {
  final AppNavItem current;
  final ValueChanged<AppNavItem>? onTap;

  const AppBottomNav({
    super.key,
    required this.current,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          decoration: BoxDecoration(
            color: const Color(0xFF353535).withValues(alpha: 0.4),
          ),
          child: SafeArea(
            top: false,
            child: SizedBox(
              height: 65,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _NavButton(
                    item: AppNavItem.inicio,
                    current: current,
                    label: 'Inicio',
                    icon: Icons.grid_view_rounded,
                    onTap: onTap,
                  ),
                  _NavButton(
                    item: AppNavItem.reservas,
                    current: current,
                    label: 'Reservas',
                    icon: Icons.calendar_today_rounded,
                    onTap: onTap,
                  ),
                  _NavButton(
                    item: AppNavItem.equinos,
                    current: current,
                    label: 'Equinos',
                    icon: Icons.hail_rounded,
                    onTap: onTap,
                  ),
                  _NavButton(
                    item: AppNavItem.clientes,
                    current: current,
                    label: 'Clientes',
                    icon: Icons.groups_2_rounded,
                    onTap: onTap,
                  ),
                  _NavButton(
                    item: AppNavItem.mas,
                    current: current,
                    label: 'Más',
                    icon: Icons.menu_rounded,
                    onTap: onTap,
                  ),
                ],
              ),
            ),
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

  const _NavButton({
    required this.item,
    required this.current,
    required this.label,
    required this.icon,
    required this.onTap,
  });

  bool get isActive => item == current;

  @override
  Widget build(BuildContext context) {
    final fg = isActive ? const Color(0xFF131313) : const Color(0xFFC6C6C6);
    final bg = isActive ? Colors.white : Colors.transparent;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => onTap?.call(item),
        borderRadius: BorderRadius.circular(isActive ? 2 : 6),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          curve: Curves.easeOut,
          constraints: const BoxConstraints(minWidth: 58),
          height: 48,
          padding: EdgeInsets.symmetric(
            horizontal: isActive ? 16 : 8,
            vertical: isActive ? 4 : 0,
          ),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(isActive ? 2 : 6),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 18,
                color: fg,
              ),
              const SizedBox(height: 4),
              Text(
                label.toUpperCase(),
                maxLines: 1,
                overflow: TextOverflow.visible,
                style: const TextStyle(
                  fontFamily: 'Inter',
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  height: 1.5,
                  letterSpacing: 0.5,
                ).copyWith(color: fg),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
