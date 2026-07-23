import 'dart:math' as math;

import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;
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
    /// Zona muerta antes de mostrar el círculo (overscroll accidental no lo revela).
    this.activationDistance = 80,
    this.triggerDistance = 100,
    this.pointerZoneHeight = 96,
  });

  final Widget child;
  final bool enabled;
  final Future<void> Function() onTriggered;
  final double displacement;

  /// Distancia de pull antes de que aparezca el indicador.
  final double activationDistance;
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

      final overscrollPastBottom = math.max(
        0.0,
        metrics.pixels - metrics.maxScrollExtent,
      );
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
    if (last != null && DateTime.now().difference(last) < _triggerCooldown) {
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

  /// Pull visible tras la zona muerta; 0 hasta [activationDistance].
  double get _visibleDrag =>
      math.max(0.0, _effectiveDrag - widget.activationDistance);

  double get _pullRange => math.max(
    1.0,
    widget.triggerDistance - widget.activationDistance,
  );

  @override
  Widget build(BuildContext context) {
    if (!widget.enabled) return widget.child;

    final progress = (_visibleDrag / _pullRange).clamp(0.0, 1.0);
    final showIndicator = _visibleDrag > 0 || _isTriggering;

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
            bottom: widget.displacement - (_visibleDrag * 0.35),
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
  const _VoicePullIndicator({required this.progress, required this.armed});

  final double progress;
  final bool armed;

  /// Misma geometría/elevation que [RefreshProgressIndicator], con mic en vez de flecha.
  static const double _indicatorSize = 41;
  static const double _strokeWidth = 2.5;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final indicatorTheme = ProgressIndicatorTheme.of(context);
    final backgroundColor =
        indicatorTheme.refreshBackgroundColor ?? theme.canvasColor;
    final color = indicatorTheme.color ?? theme.colorScheme.primary;
    final value = armed ? null : progress.clamp(0.0, 1.0);

    return Padding(
      padding: const EdgeInsets.all(4),
      child: SizedBox.square(
        dimension: _indicatorSize,
        child: Material(
          type: MaterialType.circle,
          color: backgroundColor,
          elevation: 2,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Padding(
                padding: const EdgeInsets.all(8),
                child: CircularProgressIndicator(
                  value: value,
                  strokeWidth: _strokeWidth,
                  color: color,
                ),
              ),
              Icon(Icons.mic_rounded, size: 16, color: color),
            ],
          ),
        ),
      ),
    );
  }
}
