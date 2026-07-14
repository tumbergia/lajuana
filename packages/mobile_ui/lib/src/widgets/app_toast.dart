import 'dart:async';

import 'package:flutter/material.dart';

/// Confirmación / feedback con el SnackBar simple de la app.
void showAppToast(
  BuildContext context, {
  required String message,
  bool isError = false,
}) {
  if (!context.mounted) return;
  final messenger = ScaffoldMessenger.of(context);
  messenger.hideCurrentSnackBar();
  messenger.showSnackBar(
    SnackBar(
      content: Text(message),
      duration: Duration(milliseconds: isError ? 3600 : 2600),
    ),
  );
}

OverlayEntry? _activeTopToast;

/// Toast superior del sistema de diseño: se desliza desde la parte alta de la
/// pantalla, se mantiene unos segundos y desaparece solo. Se usa para avisos de
/// conectividad/estado que antes vivían como banners persistentes.
///
/// Solo hay un toast superior activo a la vez: mostrar uno nuevo reemplaza al
/// anterior.
void showAppTopToast(
  BuildContext context, {
  required String message,
  bool isError = false,
  IconData? icon,
}) {
  if (!context.mounted) return;
  final overlay = Overlay.maybeOf(context, rootOverlay: true);
  if (overlay == null) return;

  _activeTopToast?.remove();
  _activeTopToast = null;

  late final OverlayEntry entry;
  entry = OverlayEntry(
    builder: (ctx) => _TopToast(
      message: message,
      isError: isError,
      icon: icon,
      onDismissed: () {
        if (identical(_activeTopToast, entry)) {
          _activeTopToast = null;
        }
        entry.remove();
      },
    ),
  );
  _activeTopToast = entry;
  overlay.insert(entry);
}

class _TopToast extends StatefulWidget {
  const _TopToast({
    required this.message,
    required this.isError,
    required this.onDismissed,
    this.icon,
  });

  final String message;
  final bool isError;
  final IconData? icon;
  final VoidCallback onDismissed;

  @override
  State<_TopToast> createState() => _TopToastState();
}

class _TopToastState extends State<_TopToast>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _animation;
  Timer? _dismissTimer;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 260),
    );
    _animation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
      reverseCurve: Curves.easeInCubic,
    );
    _controller.forward();
    _dismissTimer = Timer(
      Duration(milliseconds: widget.isError ? 4200 : 3000),
      _dismiss,
    );
  }

  Future<void> _dismiss() async {
    _dismissTimer?.cancel();
    if (!mounted) return;
    await _controller.reverse();
    widget.onDismissed();
  }

  @override
  void dispose() {
    _dismissTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final bgColor =
        widget.isError ? scheme.errorContainer : scheme.secondaryContainer;
    final fgColor =
        widget.isError ? scheme.onErrorContainer : scheme.onSecondaryContainer;
    final icon = widget.icon ??
        (widget.isError ? Icons.error_outline : Icons.check_circle_outline);

    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: SafeArea(
        bottom: false,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, -1),
            end: Offset.zero,
          ).animate(_animation),
          child: FadeTransition(
            opacity: _animation,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Material(
                color: Colors.transparent,
                child: GestureDetector(
                  onTap: _dismiss,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    decoration: BoxDecoration(
                      color: bgColor,
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.18),
                          blurRadius: 16,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Row(
                      children: [
                        Icon(icon, size: 18, color: fgColor),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            widget.message,
                            style: TextStyle(
                              color: fgColor,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
