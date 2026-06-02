import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/app_colors.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'app_button.dart';

/// Estilo visual del [AppConfirmDialog].
enum DialogStyle {
  /// Afirmativo — icono primary, botón primary.
  regular,

  /// Cauteloso — icono tertiary, botón primary.
  warning,

  /// Destructivo — icono error, botón danger.
  danger,
}

/// Diálogo de confirmación reutilizable con icono, título, mensaje y botones.
///
/// Sigue el patrón visual del empty state:
///   icono → título → mensaje → botones (misma fila, estilos diferenciados).
///
/// Uso típico:
/// ```dart
/// AppConfirmDialog.show(
///   context: context,
///   icon: Icons.check_circle_outline,
///   title: 'Aprobar comprobante',
///   message: '...',
///   confirmLabel: 'Aprobar',
///   onConfirm: () { ... },
/// );
/// ```
class AppConfirmDialog extends StatelessWidget {
  const AppConfirmDialog({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    required this.confirmLabel,
    required this.onConfirm,
    this.cancelLabel = 'Cancelar',
    this.onCancel,
    this.style = DialogStyle.regular,
    this.height,
  });

  /// Muestra el diálogo envolviendo [AppConfirmDialog] en un [showDialog].
  static Future<void> show({
    required BuildContext context,
    required IconData icon,
    required String title,
    required String message,
    required String confirmLabel,
    required VoidCallback onConfirm,
    String cancelLabel = 'Cancelar',
    VoidCallback? onCancel,
    DialogStyle style = DialogStyle.regular,
    double? height,
  }) {
    return showDialog<void>(
      context: context,
      builder: (_) => AppConfirmDialog(
        icon: icon,
        title: title,
        message: message,
        confirmLabel: confirmLabel,
        onConfirm: onConfirm,
        cancelLabel: cancelLabel,
        onCancel: onCancel,
        style: style,
        height: height,
      ),
    );
  }

  /// Icono principal del diálogo.
  final IconData icon;

  /// Título del diálogo.
  final String title;

  /// Mensaje descriptivo.
  final String message;

  /// Etiqueta del botón de confirmación.
  final String confirmLabel;

  /// Callback al confirmar.
  final VoidCallback onConfirm;

  /// Etiqueta del botón de cancelar. Por defecto "Cancelar".
  final String cancelLabel;

  /// Callback al cancelar. Por defecto cierra el diálogo.
  final VoidCallback? onCancel;

  /// Estilo visual: [DialogStyle.regular] (default), [DialogStyle.warning]
  /// o [DialogStyle.danger]. Controla color del icono y variante del botón.
  final DialogStyle style;

  /// Altura fija del contenido del diálogo.
  /// Si es `null` se ajusta al contenido.
  final double? height;

  Color _iconColor(ColorScheme scheme) {
    switch (style) {
      case DialogStyle.warning:
        return scheme.tertiary;
      case DialogStyle.danger:
        return AppColors.danger;
      case DialogStyle.regular:
        return scheme.primary;
    }
  }

  AppButtonVariant _resolveConfirmVariant() {
    switch (style) {
      case DialogStyle.danger:
        return AppButtonVariant.danger;
      case DialogStyle.warning:
      case DialogStyle.regular:
        return AppButtonVariant.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    return AlertDialog(
      backgroundColor: scheme.surfaceContainerHigh,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: tokens.radiusXl,
      ),
      insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
      contentPadding: EdgeInsets.zero,
      content: Padding(
        padding: EdgeInsets.all(tokens.spaceXl),
        child: SizedBox(
          height: height,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Icono ───────────────────────────────────────────────
              Icon(icon, size: 48, color: _iconColor(scheme)),
              SizedBox(height: tokens.spaceLg),

              // ── Título ──────────────────────────────────────────────
              Text(
                title,
                textAlign: TextAlign.center,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              SizedBox(height: tokens.spaceSm),

              // ── Mensaje ─────────────────────────────────────────────
              Text(
                message,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
              SizedBox(height: tokens.spaceXl),

              // ── Botones en fila ─────────────────────────────────────
              Row(
                children: [
                  // Cancelar (secondary)
                  Expanded(
                    child: AppButton(
                      label: cancelLabel,
                      variant: AppButtonVariant.secondary,
                      onPressed: () {
                        onCancel?.call();
                        Navigator.of(context).pop();
                      },
                      expanded: true,
                      height: 48,
                    ),
                  ),
                  SizedBox(width: tokens.spaceSm),

                  // Confirmar (resuelto según style)
                  Expanded(
                    child: AppButton(
                      label: confirmLabel,
                      variant: _resolveConfirmVariant(),
                      onPressed: () {
                        onConfirm();
                        Navigator.of(context).pop();
                      },
                      expanded: true,
                      height: 48,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
