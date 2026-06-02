import 'dart:math' as math;
import 'package:flutter/material.dart';

class VoiceVisualizer extends StatefulWidget {
  final int barCount;
  final Color color;
  final double barWidth;
  final double minHeight;
  final double maxHeight;
  final double gap;
  final bool isActive;

  const VoiceVisualizer({
    super.key,
    this.barCount = 6,
    this.color = Colors.white,
    this.barWidth = 6,
    this.minHeight = 12,
    this.maxHeight = 48,
    this.gap = 6,
    this.isActive = true,
  });

  @override
  State<VoiceVisualizer> createState() => _VoiceVisualizerState();
}

class _VoiceVisualizerState extends State<VoiceVisualizer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    )..repeat(reverse: false);
  }

  @override
  void didUpdateWidget(VoiceVisualizer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isActive != oldWidget.isActive) {
      if (widget.isActive) {
        _controller.repeat(reverse: false);
      } else {
        _controller.stop();
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  double _barHeight(int index, double t) {
    final phase = (t * 2 * math.pi) + (index * 0.65);
    final wave = (math.sin(phase) + 1) / 2;
    final shaped = Curves.easeInOut.transform(wave);
    return widget.minHeight +
        (widget.maxHeight - widget.minHeight) * shaped.clamp(0.0, 1.0);
  }

  @override
  Widget build(BuildContext context) {
    final totalWidth =
        (widget.barCount * widget.barWidth) +
        ((widget.barCount - 1) * widget.gap);

    return AnimatedBuilder(
      animation: _controller,
      builder: (_, _) {
        return SizedBox(
          width: totalWidth,
          height: widget.maxHeight,
          child: Align(
            alignment: Alignment.bottomCenter,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: List.generate(widget.barCount, (index) {
                // Keep a fixed visualizer box so surrounding content does not shift.
                final height = widget.isActive
                    ? _barHeight(index, _controller.value)
                    : widget.minHeight;
                return Padding(
                  padding: EdgeInsets.only(
                    right: index == widget.barCount - 1 ? 0 : widget.gap,
                  ),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 350),
                    curve: Curves.easeOut,
                    width: widget.barWidth,
                    height: height,
                    decoration: BoxDecoration(
                      color: widget.color,
                      borderRadius: BorderRadius.circular(999),
                    ),
                  ),
                );
              }),
            ),
          ),
        );
      },
    );
  }
}
