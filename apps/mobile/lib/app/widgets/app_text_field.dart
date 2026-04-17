import 'package:flutter/material.dart';
import '../theme/theme_extensions.dart';

/// Las dos variantes de campo del mockup.
enum AppTextFieldVariant {
  /// Campo contenido sobre superficie tonal. Bordes redondeados visibles.
  filled,

  /// Campo editorial con solo línea inferior. El más usado en el mockup
  /// para búsquedas y áreas de texto de observaciones.
  underlined,
}

/// Text field encapsulado con el carácter editorial del sistema.
///
/// - Label en mayúsculas + tracking, fuera del campo (no flotante).
/// - Borde underlined o filled según variante.
/// - Focus vira al color primario.
/// - Hint en [onSurfaceVariant]; sin decoración de label flotante Material.
class AppTextField extends StatelessWidget {
  final TextEditingController? controller;

  /// Etiqueta encima del campo, en mayúsculas y tracking amplio.
  final String? label;

  final String? hintText;

  /// Widget al final del campo (ej: ícono de búsqueda, mostrar contraseña).
  final Widget? suffix;

  /// Número de líneas. null = ilimitado.
  final int? maxLines;

  final AppTextFieldVariant variant;

  final TextInputType? keyboardType;
  final ValueChanged<String>? onChanged;
  final FocusNode? focusNode;
  final bool autofocus;
  final bool readOnly;
  final VoidCallback? onTap;

  const AppTextField({
    super.key,
    this.controller,
    this.label,
    this.hintText,
    this.suffix,
    this.maxLines = 1,
    this.variant = AppTextFieldVariant.filled,
    this.keyboardType,
    this.onChanged,
    this.focusNode,
    this.autofocus = false,
    this.readOnly = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    // ── Borders ────────────────────────────────────────────────────────────
    InputBorder underline(Color color, [double width = 1.0]) =>
        UnderlineInputBorder(
          borderSide: BorderSide(color: color, width: width),
        );

    InputBorder outline(Color color, [double width = 1.0]) =>
        OutlineInputBorder(
          borderRadius: tokens.radiusMd,
          borderSide: BorderSide(color: color, width: width),
        );

    final (enabledBorder, focusedBorder, baseBorder) = switch (variant) {
      AppTextFieldVariant.underlined => (
        underline(scheme.outlineVariant),
        underline(scheme.primary, 1.4),
        underline(scheme.outlineVariant),
      ),
      AppTextFieldVariant.filled => (
        outline(scheme.outlineVariant),
        outline(scheme.primary, 1.2),
        outline(scheme.outlineVariant),
      ),
    };

    // ── Content padding ────────────────────────────────────────────────────
    final isMultiline = maxLines == null || maxLines! > 1;
    final contentPadding = switch (variant) {
      AppTextFieldVariant.underlined => EdgeInsets.symmetric(
        vertical: isMultiline ? tokens.spaceLg : 12,
      ),
      AppTextFieldVariant.filled => EdgeInsets.symmetric(
        horizontal: tokens.spaceLg,
        vertical: isMultiline ? tokens.spaceLg : 14,
      ),
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Label externo
        if (label != null) ...[
          Text(
            label!.toUpperCase(),
            style: theme.textTheme.labelSmall?.copyWith(
              color: scheme.onSurfaceVariant,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.8,
            ),
          ),
          SizedBox(height: tokens.spaceSm),
        ],

        TextField(
          controller: controller,
          focusNode: focusNode,
          autofocus: autofocus,
          readOnly: readOnly,
          onTap: onTap,
          maxLines: maxLines,
          keyboardType: keyboardType,
          onChanged: onChanged,
          style: theme.textTheme.bodyMedium?.copyWith(color: scheme.onSurface),
          decoration: InputDecoration(
            hintText: hintText,
            hintStyle: theme.textTheme.bodyMedium?.copyWith(
              color: scheme.onSurfaceVariant,
            ),
            suffixIcon: suffix,
            isDense: true,
            filled: variant == AppTextFieldVariant.filled,
            fillColor: variant == AppTextFieldVariant.filled
                ? scheme.surfaceContainerLow
                : null,
            contentPadding: contentPadding,
            enabledBorder: enabledBorder,
            focusedBorder: focusedBorder,
            border: baseBorder,
            // Sin label flotante — usamos label externo
            labelText: null,
          ),
        ),
      ],
    );
  }
}
