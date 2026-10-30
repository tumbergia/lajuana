import 'dart:math' show pi;

import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';

/// Tono de superficie para AppCard.
enum AppCardTone {
  /// surface-container (#1F1F1F dark)
  surface,

  /// surface-container-highest (#353535 dark) — el más usado en el mockup
  high,

  /// surface-container-low (#1B1B1B dark) — para cards anidados
  low,

  /// error-container (#93000A dark) — alertas críticas con bg rojo
  error,
}

/// Card tonal sin elevación real, fiel al mockup.
///
/// ### Tonos
/// - [AppCardTone.high]  → `surfaceContainerHighest` (#353535)
/// - [AppCardTone.error] → `errorContainer` (#93000A) — bg rojo del mockup
///
/// ### Flip 3D
/// Si se pasa [backChild], el card es volteable:
/// - Tap en el frente → voltea al reverso
/// - Tap en el reverso → voltea de regreso y llama a [onTap] (redirigir)
///
/// **Por qué no hay Duplicate GlobalKey:**
/// Ambas faces quedan **siempre montadas** en el árbol via `Stack`.
/// Solo se ocultan con `Opacity(0)` e `IgnorePointer` cuando no están activas.
/// Esto evita el desmontaje/remontaje de sub-árboles durante la animación,
/// que es la causa del error de GlobalKey duplicado.
class AppCard extends StatefulWidget {
  /// Cara delantera (siempre requerida).
  final Widget child;

  /// Cara trasera opcional. Si se provee, activa el flip 3D.
  final Widget? backChild;

  final AppCardTone tone;

  /// Padding interno. Por defecto: tokens.spaceLg.
  final EdgeInsetsGeometry? padding;

  /// Barra de acento de 4px en el borde izquierdo.
  final Color? accentColor;

  /// Borde sutil de [outlineVariant] alrededor del card.
  final bool outlined;

  /// Callback de tap:
  /// - Sin [backChild]: se llama al tocar el frente directamente.
  /// - Con [backChild]: se llama al tocar el reverso (para navegar).
  final VoidCallback? onTap;

  const AppCard({
    super.key,
    required this.child,
    this.backChild,
    this.tone = AppCardTone.high,
    this.padding,
    this.accentColor,
    this.outlined = false,
    this.onTap,
  });

  @override
  State<AppCard> createState() => _AppCardState();
}

class _AppCardState extends State<AppCard> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 440),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  bool get _isFlipped => _ctrl.status == AnimationStatus.completed;

  void _handleTap() {
    if (widget.backChild != null) {
      if (_isFlipped) {
        _ctrl.reverse();
        widget.onTap?.call();
      } else {
        _ctrl.forward();
      }
    } else {
      widget.onTap?.call();
    }
  }

  Color _resolveBg(ColorScheme scheme) {
    switch (widget.tone) {
      case AppCardTone.surface:
        return scheme.surfaceContainer;
      case AppCardTone.high:
        return scheme.surfaceContainerHighest;
      case AppCardTone.low:
        return scheme.surfaceContainerLow;
      case AppCardTone.error:
        return scheme.errorContainer;
    }
  }

  /// Envuelve [content] en la decoración del card (borde, color, acento).
  ///
  /// [showAccent] controla si se dibuja la barra lateral (solo en el frente).
  Widget _decorate(
    BuildContext context,
    Widget content, {
    bool showAccent = true,
  }) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;
    final radius = tokens.radiusLg;

    return ClipRRect(
      borderRadius: radius,
      child: Container(
        decoration: BoxDecoration(
          color: _resolveBg(scheme),
          borderRadius: radius,
          border: widget.outlined
              ? Border.all(color: scheme.outlineVariant.withValues(alpha: 0.4))
              : null,
        ),
        // Stack + Positioned accent avoids IntrinsicHeight, which breaks
        // LayoutBuilder-based children (e.g. fl_chart).
        child: Stack(
          children: [
            if (showAccent && widget.accentColor != null)
              Positioned(
                left: 0,
                top: 0,
                bottom: 0,
                width: 4,
                child: ColoredBox(color: widget.accentColor!),
              ),
            Padding(
              padding: EdgeInsets.only(
                left: showAccent && widget.accentColor != null ? 4 : 0,
              ),
              child: Padding(
                padding: widget.padding ?? EdgeInsets.all(tokens.spaceLg),
                child: content,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final scheme = Theme.of(context).colorScheme;

    // ── Sin flip: card simple con ripple opcional ─────────────────────────
    if (widget.backChild == null) {
      final face = _decorate(context, widget.child);

      if (widget.onTap == null) return face;

      return Material(
        color: Colors.transparent,
        borderRadius: tokens.radiusLg,
        child: InkWell(
          borderRadius: tokens.radiusLg,
          onTap: widget.onTap,
          splashColor: scheme.onSurface.withValues(alpha: 0.06),
          highlightColor: scheme.onSurface.withValues(alpha: 0.04),
          child: face,
        ),
      );
    }

    // ── Con flip 3D ───────────────────────────────────────────────────────
    //
    // Tanto el frente como el reverso permanecen SIEMPRE MONTADOS en el árbol
    // (Stack + Positioned.fill). Esto es crítico:
    //
    //   ❌ Condicional en el builder → desmonta/remonta sub-árboles en cada frame
    //      → Duplicate GlobalKey si esos sub-árboles tienen widgets con key interna
    //
    //   ✓ Siempre montados → Opacity(0) + IgnorePointer los oculta visualmente
    //      → Flip suave sin errores de GlobalKey
    //
    // Adicionalmente, cada face se pasa como `child` (no dentro del `builder`)
    // para que el AnimatedBuilder NO rebuilde la sub-árbol en cada tick;
    // solo recalcula la Transform. Esto es O(1) en rendering cost.
    //
    // Técnica de rotación:
    //   Frente: rota de 0 → π (de cara → de espaldas)
    //   Reverso: rota de -π → 0 (de espaldas → de cara)
    //   setEntry(3,2) agrega perspectiva para efecto 3D real.

    final frontFace = _decorate(context, widget.child, showAccent: true);
    final backFace = _decorate(
      context,
      // El contenido del reverso se pre-rota π para aparecer derecho
      Transform(
        alignment: Alignment.center,
        transform: Matrix4.identity()..rotateY(pi),
        child: widget.backChild!,
      ),
      showAccent: false,
    );

    return GestureDetector(
      onTap: _handleTap,
      child: Stack(
        children: [
          // ── Cara delantera (define el tamaño del Stack) ───────────────
          AnimatedBuilder(
            animation: _ctrl,
            child: frontFace, // construido UNA vez, no en cada tick
            builder: (_, child) {
              final t = Curves.easeInOutCubic.transform(_ctrl.value);
              final angle = t * pi;
              final isActive = angle < pi / 2;

              return IgnorePointer(
                ignoring: !isActive,
                child: Opacity(
                  opacity: isActive ? 1.0 : 0.0,
                  child: Transform(
                    alignment: Alignment.center,
                    transform: Matrix4.identity()
                      ..setEntry(3, 2, 0.0012)
                      ..rotateY(angle),
                    child: child,
                  ),
                ),
              );
            },
          ),

          // ── Cara trasera (se superpone al frente, mismo tamaño) ───────
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _ctrl,
              child: backFace, // construido UNA vez, no en cada tick
              builder: (_, child) {
                final t = Curves.easeInOutCubic.transform(_ctrl.value);
                final angle = t * pi;
                final isActive = angle >= pi / 2;

                return IgnorePointer(
                  ignoring: !isActive,
                  child: Opacity(
                    opacity: isActive ? 1.0 : 0.0,
                    child: Transform(
                      alignment: Alignment.center,
                      transform: Matrix4.identity()
                        ..setEntry(3, 2, 0.0012)
                        ..rotateY(angle - pi),
                      child: child,
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
