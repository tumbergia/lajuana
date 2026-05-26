import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/theme_extensions.dart';

/// Las familias de botón del mockup Equus Command.
enum AppButtonVariant {
  /// Fondo primario (blanco en dark), texto oscuro. CTA principal.
  primary,

  /// Fondo tonal oscuro + borde tenue. Acción secundaria.
  secondary,

  /// Sin fondo, texto muted. Acción ligera o ghost.
  ghost,

  /// Fondo error, texto onError. Acción destructiva.
  danger,
}

/// Botón editorial fiel al mockup.
///
/// - Texto en ALLCAPS con letter-spacing amplio (Manrope/Inter bold)
/// - Escala nativa con [AnimatedScale] en press (96%) — sin AnimationController manual
/// - Ripple correcto: [Material] porta el color de fondo, no [Container]
/// - Altura y padding fijos para coherencia cross-screen
class AppButton extends StatefulWidget {
  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final AppButtonVariant variant;

  /// Si true, ocupa todo el ancho disponible.
  final bool expanded;

  /// Altura del botón. Por defecto 52.
  final double height;

  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.variant = AppButtonVariant.primary,
    this.expanded = false,
    this.height = 52,
  });

  @override
  State<AppButton> createState() => _AppButtonState();
}

class _AppButtonState extends State<AppButton> {
  bool _pressed = false;

  void _onTapDown(TapDownDetails _) {
    if (mounted) setState(() => _pressed = true);
  }

  void _onTapUp(TapUpDetails _) {
    if (mounted) setState(() => _pressed = false);
  }

  void _onTapCancel() {
    if (mounted) setState(() => _pressed = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;
    final isDisabled = widget.onPressed == null;

    // ── Colores por variante ───────────────────────────────────────────────
    // Usando if/else en lugar de switch-expression para máxima compat con
    // versiones de Flutter y el compilador DDC (web).
    // Usando withOpacity() en lugar de withValues() por compatibilidad con
    // Flutter < 3.27.
    final Color bg;
    final Color fg;
    final BorderSide? side;

    if (widget.variant == AppButtonVariant.primary) {
      bg = isDisabled
          ? scheme.onSurface.withValues(alpha: 0.12)
          : scheme.primary;
      fg = isDisabled
          ? scheme.onSurface.withValues(alpha: 0.38)
          : scheme.onPrimary;
      side = null;
    } else if (widget.variant == AppButtonVariant.secondary) {
      bg = scheme.surfaceContainerLow;
      fg = isDisabled
          ? scheme.onSurface.withValues(alpha: 0.38)
          : scheme.onSurface;
      side = BorderSide(
        color: scheme.outlineVariant.withValues(alpha: isDisabled ? 0.2 : 0.5),
      );
    } else if (widget.variant == AppButtonVariant.danger) {
      bg = isDisabled
          ? scheme.onSurface.withValues(alpha: 0.12)
          : AppColors.danger;
      fg = isDisabled
          ? scheme.onSurface.withValues(alpha: 0.38)
          : Colors.white;
      side = null;
    } else {
      // ghost
      bg = Colors.transparent;
      fg = isDisabled
          ? scheme.onSurface.withValues(alpha: 0.38)
          : scheme.onSurfaceVariant;
      side = null;
    }

    // ── Contenido ─────────────────────────────────────────────────────────
    final rowContent = Row(
      mainAxisSize: widget.expanded ? MainAxisSize.max : MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (widget.icon != null) ...[
          Icon(widget.icon, size: 18, color: fg),
          SizedBox(width: tokens.spaceSm),
        ],
        Text(
          widget.label.toUpperCase(),
          overflow: TextOverflow.ellipsis,
          softWrap: false,
          style: theme.textTheme.labelLarge?.copyWith(
            color: fg,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.4,
          ),
        ),
      ],
    );

    // ── Layout: borde → Material(color) → InkWell → SizedBox ─────────────
    //
    // Material lleva el color real para que el ripple de InkWell
    // se vea correctamente. SizedBox fija la altura sin que el
    // contenido la altere (evita la inconsistencia de tamaños).
    Widget button = SizedBox(
      height: widget.height,
      width: widget.expanded ? double.infinity : null,
      child: Material(
        color: bg,
        borderRadius: tokens.radiusMd,
        child: InkWell(
          borderRadius: tokens.radiusMd,
          onTap: isDisabled ? null : widget.onPressed,
          onTapDown: isDisabled ? null : _onTapDown,
          onTapUp: isDisabled ? null : _onTapUp,
          onTapCancel: isDisabled ? null : _onTapCancel,
          splashColor: fg.withValues(alpha: 0.12),
          highlightColor: fg.withValues(alpha: 0.06),
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: tokens.spaceLg),
            child: rowContent,
          ),
        ),
      ),
    );

    // Wrapper de borde exterior (solo secondary)
    if (side != null) {
      button = DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: tokens.radiusMd,
          border: Border.fromBorderSide(side),
        ),
        child: button,
      );
    }

    // AnimatedScale es el widget oficial de Flutter para escala en press.
    // No requiere AnimationController ni Tween manual — el framework
    // interpola automáticamente con el duration/curve dados.
    return AnimatedScale(
      scale: (_pressed && !isDisabled) ? 0.96 : 1.0,
      duration: const Duration(milliseconds: 120),
      curve: Curves.easeOut,
      child: button,
    );
  }
}
