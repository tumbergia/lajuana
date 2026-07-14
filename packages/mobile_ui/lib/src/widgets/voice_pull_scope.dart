import 'dart:math' as math;

import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

/// Pull-to-voice desde el borde inferior, espejo del [RefreshIndicator] superior.
///
/// En móvil usa overscroll al fondo del scroll. En web/desktop también acepta
/// arrastre con puntero (ratón/trackpad) desde la franja inferior.
class VoicePullScope extends StatefulWidget {
  const VoicePullScope({
    super.key,
    required this.child,
    required this.enabled,
    required this.onTriggered,
    this.displacement = 48,
    this.triggerDistance = 110,
    this.pointerZoneHeight = 96,
  });

  final Widget child;
  final bool enabled;
  final Future<void> Function() onTriggered;
  final double displacement;
  final double triggerDistance;
  final double pointerZoneHeight;

  @override
  State<VoicePullScope> createState() => _VoicePullScopeState();
}

class _VoicePullScopeState extends State<VoicePullScope>
    with SingleTickerProviderStateMixin {
  /// Evita re-disparar el mic por overscroll residual / gestos dobles.
  static const Duration _triggerCooldown = Duration(seconds: 3);

  double _dragOffset = 0;
  bool _atBottom = false;
  bool _isTriggering = false;
  DateTime? _lastTriggeredAt;
  ScrollMetrics? _lastMetrics;
  int? _activePointer;
  double _pointerDragStart = 0;
  late AnimationController _snapController;
  late Animation<double> _snapAnimation;

  bool get _usePointerFallback {
    if (kIsWeb) return true;
    switch (defaultTargetPlatform) {
      case TargetPlatform.linux:
      case TargetPlatform.macOS:
      case TargetPlatform.windows:
        return true;
      default:
        return false;
    }
  }

  @override
  void initState() {
    super.initState();
    _snapController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 220),
    );
    _snapAnimation = CurvedAnimation(
      parent: _snapController,
      curve: Curves.easeOutCubic,
    );
    _snapController.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _dragOffset = 0;
        if (mounted) setState(() {});
      }
    });
    _snapController.addListener(() {
      if (_snapController.isAnimating && mounted) {
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    _snapController.dispose();
    super.dispose();
  }

  bool _isAtBottom(ScrollMetrics metrics) {
    return metrics.extentAfter <= 0.5 ||
        metrics.pixels >= metrics.maxScrollExtent - 0.5;
  }

  bool get _canPullNow {
    final metrics = _lastMetrics;
    if (metrics == null) return true;
    return _isAtBottom(metrics);
  }

  bool _handleScrollNotification(ScrollNotification notification) {
    if (!widget.enabled || _isTriggering) return false;

    final metrics = notification.metrics;
    if (metrics.axis != Axis.vertical) return false;
    _lastMetrics = metrics;

    if (notification is ScrollStartNotification) {
      _atBottom = _isAtBottom(metrics);
      if (!_atBottom) {
        _resetDrag();
      }
      return false;
    }

    if (notification is ScrollUpdateNotification) {
      _atBottom = _isAtBottom(metrics);
      if (!_atBottom) {
        _resetDrag();
        return false;
      }

      final overscrollPastBottom =
          math.max(0.0, metrics.pixels - metrics.maxScrollExtent);
      final delta = notification.scrollDelta ?? 0;

      var nextOffset = _dragOffset;
      if (overscrollPastBottom > 0) {
        nextOffset = overscrollPastBottom;
      } else if (delta > 0 && _dragOffset > 0) {
        nextOffset = math.max(0, _dragOffset - delta);
      }

      _setDrag(nextOffset);
      return false;
    }

    if (notification is OverscrollNotification && _isAtBottom(metrics)) {
      if (notification.overscroll > 0) {
        _setDrag(
          math.max(
            _dragOffset,
            metrics.pixels - metrics.maxScrollExtent + notification.overscroll,
          ),
        );
      }
      return false;
    }

    if (notification is ScrollEndNotification) {
      if (_activePointer == null) {
        _onRelease();
      }
      _atBottom = false;
      return false;
    }

    return false;
  }

  void _onPointerDown(PointerDownEvent event) {
    if (!_usePointerFallback || _isTriggering) return;
    if (event.kind == PointerDeviceKind.touch) return;
    if (!_canPullNow) return;

    _activePointer = event.pointer;
    _pointerDragStart = event.position.dy;
  }

  void _onPointerMove(PointerMoveEvent event) {
    if (event.pointer != _activePointer || _isTriggering) return;
    if (!_canPullNow) {
      _resetDrag();
      return;
    }

    final delta = _pointerDragStart - event.position.dy;
    if (delta > 0) {
      _setDrag(delta);
    } else if (_dragOffset > 0) {
      _setDrag(math.max(0, _dragOffset + delta));
    }
  }

  void _onPointerEnd(int pointer) {
    if (pointer != _activePointer) return;
    _activePointer = null;
    _onRelease();
  }

  void _onRelease() {
    if (_dragOffset >= widget.triggerDistance) {
      _triggerVoice();
    } else {
      _animateReset();
    }
  }

  void _setDrag(double value) {
    final clamped = value.clamp(0.0, widget.triggerDistance * 1.35);
    if ((clamped - _dragOffset).abs() < 0.5) return;
    _snapController.stop();
    _dragOffset = clamped;
    setState(() {});
  }

  void _resetDrag() {
    if (_dragOffset == 0) return;
    _dragOffset = 0;
    if (mounted) setState(() {});
  }

  void _animateReset() {
    if (_dragOffset <= 0) return;
    _snapAnimation = Tween<double>(begin: _dragOffset, end: 0).animate(
      CurvedAnimation(parent: _snapController, curve: Curves.easeOutCubic),
    );
    _snapController
      ..reset()
      ..forward();
  }

  Future<void> _triggerVoice() async {
    if (_isTriggering) return;
    final last = _lastTriggeredAt;
    if (last != null &&
        DateTime.now().difference(last) < _triggerCooldown) {
      _animateReset();
      return;
    }
    _isTriggering = true;
    _lastTriggeredAt = DateTime.now();
    setState(() {});

    try {
      await widget.onTriggered();
    } finally {
      _isTriggering = false;
      _animateReset();
    }
  }

  double get _effectiveDrag {
    if (_snapController.isAnimating) {
      return _snapAnimation.value;
    }
    return _dragOffset;
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.enabled) return widget.child;

    final progress = (_effectiveDrag / widget.triggerDistance).clamp(0.0, 1.0);
    final showIndicator = _effectiveDrag > 0 || _isTriggering;

    return Stack(
      clipBehavior: Clip.none,
      children: [
        NotificationListener<ScrollNotification>(
          onNotification: _handleScrollNotification,
          child: widget.child,
        ),
        if (_usePointerFallback)
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            height: widget.pointerZoneHeight,
            child: Listener(
              behavior: HitTestBehavior.translucent,
              onPointerDown: _onPointerDown,
              onPointerMove: _onPointerMove,
              onPointerUp: (event) => _onPointerEnd(event.pointer),
              onPointerCancel: (event) => _onPointerEnd(event.pointer),
            ),
          ),
        if (showIndicator)
          Positioned(
            left: 0,
            right: 0,
            bottom: widget.displacement - (_effectiveDrag * 0.35),
            child: IgnorePointer(
              child: Center(
                child: _VoicePullIndicator(
                  progress: _isTriggering ? 1 : progress,
                  armed: progress >= 1 || _isTriggering,
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _VoicePullIndicator extends StatelessWidget {
  const _VoicePullIndicator({
    required this.progress,
    required this.armed,
  });

  final double progress;
  final bool armed;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final size = 36.0 + (progress * 8);

    return AnimatedContainer(
      duration: const Duration(milliseconds: 120),
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: isDark ? Colors.white : scheme.primary,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: (isDark ? Colors.white : scheme.primary)
                .withValues(alpha: 0.12 * progress),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: size - 6,
            height: size - 6,
            child: CircularProgressIndicator(
              value: armed ? null : progress,
              strokeWidth: 2.4,
              color: isDark ? const Color(0xFF131313) : scheme.onPrimary,
              backgroundColor: (isDark ? const Color(0xFF131313) : scheme.onPrimary)
                  .withValues(alpha: 0.18),
            ),
          ),
          Icon(
            Icons.mic_rounded,
            size: 16 + (progress * 2),
            color: isDark ? const Color(0xFF131313) : scheme.onPrimary,
          ),
        ],
      ),
    );
  }
}
