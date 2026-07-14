import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

/// Solid tile + contrasting glyph — same idea as notification icon chips.
({Color background, Color foreground}) leadCategoryIconColors(
  BuildContext context,
  String categoryId,
) {
  final scheme = Theme.of(context).colorScheme;
  switch (categoryId) {
    case 'accion':
      return (
        background: AppColors.warning,
        foreground: const Color(0xFF1A1A1A),
      );
    case 'reservas':
      return (background: scheme.primary, foreground: scheme.onPrimary);
    case 'dinero':
      return (background: AppColors.success, foreground: Colors.white);
    case 'eq_operacion':
      return (
        background: const Color(0xFF00897B),
        foreground: Colors.white,
      );
    case 'eq_salud':
      return (background: AppColors.danger, foreground: Colors.white);
    case 'personas':
      return (
        background: const Color(0xFF5C6BC0),
        foreground: Colors.white,
      );
    case 'catalogo':
      return (background: scheme.onSurface, foreground: scheme.surface);
    default:
      return (background: scheme.primary, foreground: scheme.onPrimary);
  }
}

/// Solid accent bar / pin highlight color for a category.
Color leadCategoryAccent(BuildContext context, String categoryId) {
  return leadCategoryIconColors(context, categoryId).background;
}
