import 'package:flutter/material.dart';
import 'package:mobile_ui/mobile_ui.dart';

/// Skeleton shaped like a chart while a module loads (cold start).
class AppChartLoadingSkeleton extends StatefulWidget {
  const AppChartLoadingSkeleton({
    super.key,
    this.height,
    this.label = 'Cargando gráfica…',
    this.variant = ChartSkeletonVariant.line,
  });

  final double? height;
  final String label;
  final ChartSkeletonVariant variant;

  @override
  State<AppChartLoadingSkeleton> createState() =>
      _AppChartLoadingSkeletonState();
}

enum ChartSkeletonVariant { line, bars, donut, sparkline }

class _AppChartLoadingSkeletonState extends State<AppChartLoadingSkeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    );
    if (!const bool.fromEnvironment('FLUTTER_TEST')) {
      // Started in didChangeDependencies when animations allowed.
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      _pulse.stop();
      _pulse.value = 0.55;
    } else if (!_pulse.isAnimating) {
      _pulse.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).analyticsTokens;
    final scheme = Theme.of(context).colorScheme;
    final height = widget.height ??
        (widget.variant == ChartSkeletonVariant.sparkline
            ? tokens.chartHeightCompact
            : tokens.chartHeightStandard);

    return Semantics(
      label: widget.label,
      child: AnimatedBuilder(
        animation: _pulse,
        builder: (context, _) {
          final t = 0.35 + (_pulse.value * 0.35);
          final fill = Color.lerp(
            scheme.surfaceContainerHighest,
            scheme.outlineVariant,
            t,
          )!;
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                height: height,
                width: double.infinity,
                child: CustomPaint(
                  painter: _SkeletonPainter(
                    color: fill,
                    variant: widget.variant,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                widget.label,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _SkeletonPainter extends CustomPainter {
  _SkeletonPainter({required this.color, required this.variant});

  final Color color;
  final ChartSkeletonVariant variant;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = color;
    switch (variant) {
      case ChartSkeletonVariant.sparkline:
      case ChartSkeletonVariant.line:
        final path = Path()
          ..moveTo(0, size.height * 0.7)
          ..quadraticBezierTo(
            size.width * 0.25,
            size.height * 0.2,
            size.width * 0.5,
            size.height * 0.55,
          )
          ..quadraticBezierTo(
            size.width * 0.75,
            size.height * 0.85,
            size.width,
            size.height * 0.35,
          );
        canvas.drawPath(
          path,
          paint
            ..style = PaintingStyle.stroke
            ..strokeWidth = 3
            ..strokeCap = StrokeCap.round,
        );
      case ChartSkeletonVariant.bars:
        const n = 5;
        final gap = size.width * 0.04;
        final w = (size.width - gap * (n + 1)) / n;
        for (var i = 0; i < n; i++) {
          final h = size.height * (0.35 + (i % 3) * 0.2);
          final left = gap + i * (w + gap);
          canvas.drawRRect(
            RRect.fromRectAndRadius(
              Rect.fromLTWH(left, size.height - h, w, h),
              const Radius.circular(4),
            ),
            paint..style = PaintingStyle.fill,
          );
        }
      case ChartSkeletonVariant.donut:
        final c = Offset(size.width / 2, size.height / 2);
        final r = size.shortestSide * 0.35;
        canvas.drawCircle(
          c,
          r,
          paint
            ..style = PaintingStyle.stroke
            ..strokeWidth = 18,
        );
    }
  }

  @override
  bool shouldRepaint(covariant _SkeletonPainter oldDelegate) =>
      oldDelegate.color != color || oldDelegate.variant != variant;
}

/// Soft banner while existing chart data refreshes in the background.
///
/// Deprecated for UX: Inicio/Dashboard use a single global loader instead of
/// per-card "Actualizando" badges. Kept as a no-op so call sites compile.
class ChartRefreshingBadge extends StatelessWidget {
  const ChartRefreshingBadge({super.key});

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
