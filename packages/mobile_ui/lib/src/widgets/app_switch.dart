import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/app_radii.dart';

/// Switch deslizante con geometría cuadrada alineada a [AppRadii.lg].
class AppSwitch extends StatelessWidget {
  const AppSwitch({
    super.key,
    required this.value,
    required this.onChanged,
    this.semanticsLabel,
  });

  static const double trackWidth = 48;
  static const double trackHeight = 28;
  static const double thumbPadding = 3;
  static const double thumbSize = trackHeight - (thumbPadding * 2);
  static const Duration animationDuration = Duration(milliseconds: 200);

  final bool value;
  final ValueChanged<bool>? onChanged;
  final String? semanticsLabel;

  bool get _enabled => onChanged != null;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final enabled = _enabled;

    final Color trackColor;
    final Color thumbColor;

    if (!enabled) {
      trackColor = scheme.onSurface.withValues(alpha: 0.12);
      thumbColor = scheme.onSurface.withValues(alpha: 0.38);
    } else if (value) {
      trackColor = scheme.primary;
      thumbColor = scheme.onPrimary;
    } else {
      trackColor = scheme.outlineVariant.withValues(alpha: 0.35);
      thumbColor = scheme.onSurfaceVariant;
    }

    return Semantics(
      label: semanticsLabel,
      button: true,
      enabled: enabled,
      toggled: value,
      child: GestureDetector(
        onTap: enabled ? () => onChanged!(!value) : null,
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: animationDuration,
          curve: Curves.easeOut,
          width: trackWidth,
          height: trackHeight,
          padding: const EdgeInsets.all(thumbPadding),
          decoration: BoxDecoration(
            color: trackColor,
            borderRadius: AppRadii.radiusLg,
          ),
          child: AnimatedAlign(
            duration: animationDuration,
            curve: Curves.easeOut,
            alignment: value ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              width: thumbSize,
              height: thumbSize,
              decoration: BoxDecoration(
                color: thumbColor,
                borderRadius: AppRadii.radiusLg,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
