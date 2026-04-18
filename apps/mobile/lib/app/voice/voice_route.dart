import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'voice_context.dart';
import 'voice_screen.dart';

Future<void> openVoiceScreen(
  BuildContext context, {
  required VoiceContext voiceContext,
  required Offset origin,
  double initialRadius = 0,
}) {
  return Navigator.of(context).push(
    PageRouteBuilder(
      transitionDuration: const Duration(milliseconds: 460),
      reverseTransitionDuration: const Duration(milliseconds: 320),
      opaque: true,
      pageBuilder: (_, _, _) => VoiceScreen(voiceContext: voiceContext),
      transitionsBuilder: (context, animation, _, child) {
        return _CircularRevealTransition(
          animation: animation,
          origin: origin,
          initialRadius: initialRadius,
          child: child,
        );
      },
    ),
  );
}

class _CircularRevealTransition extends AnimatedWidget {
  final Offset origin;
  final double initialRadius;
  final Widget child;

  const _CircularRevealTransition({
    required Animation<double> animation,
    required this.origin,
    required this.initialRadius,
    required this.child,
  }) : super(listenable: animation);

  Animation<double> get animation => listenable as Animation<double>;

  @override
  Widget build(BuildContext context) {
    return ClipPath(
      clipper: _CircularRevealClipper(
        origin: origin,
        initialRadius: initialRadius,
        fraction: CurvedAnimation(
          parent: animation,
          curve: Curves.fastOutSlowIn,
          reverseCurve: Curves.easeInCubic,
        ).value,
      ),
      child: child,
    );
  }
}

class _CircularRevealClipper extends CustomClipper<Path> {
  final Offset origin;
  final double initialRadius;
  final double fraction;

  _CircularRevealClipper({
    required this.origin,
    required this.initialRadius,
    required this.fraction,
  });

  @override
  Path getClip(Size size) {
    final maxRadius = _calcMaxRadius(size, origin);
    final radius = initialRadius + (maxRadius - initialRadius) * fraction;

    return Path()..addOval(Rect.fromCircle(center: origin, radius: radius));
  }

  double _calcMaxRadius(Size size, Offset origin) {
    final dx = math.max(origin.dx, size.width - origin.dx);
    final dy = math.max(origin.dy, size.height - origin.dy);
    return math.sqrt(dx * dx + dy * dy);
  }

  @override
  bool shouldReclip(_CircularRevealClipper oldClipper) {
    return oldClipper.origin != origin ||
        oldClipper.initialRadius != initialRadius ||
        oldClipper.fraction != fraction;
  }
}
