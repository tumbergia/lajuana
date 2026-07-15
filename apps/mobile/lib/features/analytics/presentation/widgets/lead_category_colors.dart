import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

/// Solid tile + contrasting glyph — delegates to analytics domain tokens.
({Color background, Color foreground}) leadCategoryIconColors(
  BuildContext context,
  String categoryId,
) {
  // Map legacy lead category ids → analytics v2 domain keys.
  final domain = switch (categoryId) {
    'accion' => 'action',
    'reservas' => 'reservations',
    'dinero' => 'money',
    'catalogo' => 'experiences',
    'personas' => 'participants',
    'eq_operacion' => 'operations',
    'eq_salud' => 'equines',
    _ => categoryId,
  };
  final accent = Theme.of(context).analyticsTokens.domainColor(domain);
  final fg = ThemeData.estimateBrightnessForColor(accent) == Brightness.dark
      ? Colors.white
      : const Color(0xFF1A1A1A);
  return (background: accent, foreground: fg);
}

/// Solid accent bar / pin highlight color for a category.
Color leadCategoryAccent(BuildContext context, String categoryId) {
  return leadCategoryIconColors(context, categoryId).background;
}
