import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'app_assignment_card.dart';

class AppAssignmentListItem extends StatelessWidget {
  const AppAssignmentListItem({
    super.key,
    required this.participant,
    required this.equine,
    required this.saddleLabel,
    this.isFinalized = false,
    this.onChangeEquine,
    this.onChangeSaddle,
    this.onRemoveAssignment,
    this.onRemoveSaddle,
    this.onRevertFinalize,
    this.validationMessage,
    this.state = AppAssignmentCardState.ok,
    this.safetyFlags = const [],
  });

  final AppAssignmentParticipantData participant;
  final AppAssignmentEquineData equine;
  final String saddleLabel;
  final bool isFinalized;
  final VoidCallback? onChangeEquine;
  final VoidCallback? onChangeSaddle;
  final VoidCallback? onRemoveAssignment;
  final VoidCallback? onRemoveSaddle;
  final VoidCallback? onRevertFinalize;
  final String? validationMessage;
  final AppAssignmentCardState state;
  final List<String> safetyFlags;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;
    final accent = _accentForState(scheme);

    return Container(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: tokens.radiusLg,
        border: Border.all(color: accent.withValues(alpha: 0.24), width: 0.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 4,
            decoration: BoxDecoration(
              color: accent,
              borderRadius: BorderRadius.only(
                topLeft: tokens.radiusLg.topLeft,
                bottomLeft: tokens.radiusLg.bottomLeft,
              ),
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _InfoColumn(
                    label: 'Participante',
                    title: participant.name,
                    titleIcon: Icons.person_outline_rounded,
                    titleIconColor: accent,
                    subtitle: _participantSubtitle(),
                  ),
                  const SizedBox(height: 16),
                  _EquineInlineBlock(
                    equine: equine,
                    isAssigned: equine.name != 'Sin asignar',
                    isFinalized: isFinalized,
                    onAction: onChangeEquine,
                    onRemoveAssignment: onRemoveAssignment,
                    onRevertFinalize: onRevertFinalize,
                  ),
                  const SizedBox(height: 12),
                  Divider(
                    color: scheme.outlineVariant.withValues(alpha: 0.35),
                    height: 1,
                  ),
                  const SizedBox(height: 12),
                  _SaddleInlineBlock(
                    saddleLabel: saddleLabel,
                    isAssigned: saddleLabel != '—',
                    onAction: onChangeSaddle,
                    onRemoveSaddle: onRemoveSaddle,
                  ),
                  if (validationMessage != null &&
                      validationMessage != 'Pendiente de asignación') ...[
                    const SizedBox(height: 12),
                    _InlineValidationBanner(
                      message: validationMessage!,
                      state: state,
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _accentForState(ColorScheme scheme) {
    switch (state) {
      case AppAssignmentCardState.ok:
        return const Color(0xFF2E7D32);
      case AppAssignmentCardState.warning:
        return scheme.tertiary;
      case AppAssignmentCardState.error:
        return scheme.error;
    }
  }

  String _participantSubtitle() {
    final parts = <String>[participant.weightLabel];
    if (participant.ageLabel != null) {
      parts.add(participant.ageLabel!);
    }
    return parts.join(' · ');
  }
}

class _InfoColumn extends StatelessWidget {
  const _InfoColumn({
    required this.label,
    required this.title,
    required this.titleIcon,
    required this.titleIconColor,
    this.subtitle,
  });

  final String label;
  final String title;
  final IconData titleIcon;
  final Color titleIconColor;
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              label.toUpperCase(),
              style: theme.textTheme.labelSmall?.copyWith(
                color: scheme.onSurfaceVariant,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.7,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(titleIcon, size: 16, color: titleIconColor),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  if (subtitle != null) ...[
                    const SizedBox(height: 6),
                    Text(
                      subtitle!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _EquineInlineBlock extends StatelessWidget {
  const _EquineInlineBlock({
    required this.equine,
    required this.isAssigned,
    required this.isFinalized,
    this.onAction,
    this.onRemoveAssignment,
    this.onRevertFinalize,
  });

  final AppAssignmentEquineData equine;
  final bool isAssigned;
  final bool isFinalized;
  final VoidCallback? onAction;
  final VoidCallback? onRemoveAssignment;
  final VoidCallback? onRevertFinalize;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    if (isAssigned) {
      final buttons = <_InlineAction>[
        if (onAction != null)
          _InlineAction(
            label: 'Cambiar',
            icon: Icons.swap_horiz_rounded,
            variant: AppButtonVariant.secondary,
            onPressed: onAction,
          ),
        if (onRemoveAssignment != null && !isFinalized)
          _InlineAction(
            label: 'Quitar',
            icon: Icons.delete_outline_rounded,
            variant: AppButtonVariant.danger,
            onPressed: onRemoveAssignment,
          ),
        if (onRevertFinalize != null && isFinalized)
          _InlineAction(
            label: 'Volver',
            icon: Icons.undo_rounded,
            variant: AppButtonVariant.secondary,
            onPressed: onRevertFinalize,
          ),
      ];

      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 14),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerLow,
                borderRadius: theme.appTokens.radiusMd,
                border: Border.all(
                  color: scheme.outlineVariant.withValues(alpha: 0.25),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  CustomPaint(
                    painter: _DashedRectPainter(
                      color: scheme.outlineVariant.withValues(alpha: 0.5),
                      strokeWidth: 1,
                      dashWidth: 5,
                      gapWidth: 3,
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(2),
                      child: _EquineThumb(image: equine.image),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      equine.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.start,
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (buttons.isNotEmpty) ...[
            const SizedBox(width: 10),
            SizedBox(
              width: 44,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final button in buttons) ...[
                    _CompactActionButton(
                      label: button.label,
                      icon: button.icon,
                      variant: button.variant,
                      onPressed: button.onPressed,
                    ),
                    if (button != buttons.last) const SizedBox(height: 8),
                  ],
                ],
              ),
            ),
          ],
        ],
      );
    }

    return _AssignmentPrompt(
      label: 'Asignar equino',
      onTap: onAction,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.add_rounded, size: 18, color: scheme.primary),
          const SizedBox(width: 6),
          Text(
            'Asignar equino',
            style: theme.textTheme.labelLarge?.copyWith(
              color: scheme.primary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _SaddleInlineBlock extends StatelessWidget {
  const _SaddleInlineBlock({
    required this.saddleLabel,
    required this.isAssigned,
    this.onAction,
    this.onRemoveSaddle,
  });

  final String saddleLabel;
  final bool isAssigned;
  final VoidCallback? onAction;
  final VoidCallback? onRemoveSaddle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    if (isAssigned) {
      final buttons = <_InlineAction>[
        if (onAction != null)
          _InlineAction(
            label: 'Cambiar silla',
            icon: Icons.swap_horiz_rounded,
            variant: AppButtonVariant.secondary,
            onPressed: onAction,
          ),
        if (onRemoveSaddle != null)
          _InlineAction(
            label: 'Quitar silla',
            icon: Icons.delete_outline_rounded,
            variant: AppButtonVariant.danger,
            onPressed: onRemoveSaddle,
          ),
      ];

      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 14),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerLow,
                borderRadius: theme.appTokens.radiusMd,
                border: Border.all(
                  color: scheme.outlineVariant.withValues(alpha: 0.25),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  CustomPaint(
                    painter: _DashedRectPainter(
                      color: scheme.outlineVariant.withValues(alpha: 0.5),
                      strokeWidth: 1,
                      dashWidth: 5,
                      gapWidth: 3,
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(2),
                      child: SizedBox(
                        width: 42,
                        height: 42,
                        child: Icon(
                          Icons.airline_seat_recline_normal_rounded,
                          size: 24,
                          color: scheme.onSurfaceVariant,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _saddleName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.start,
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (buttons.isNotEmpty) ...[
            const SizedBox(width: 10),
            SizedBox(
              width: 44,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final button in buttons) ...[
                    _CompactActionButton(
                      label: button.label,
                      icon: button.icon,
                      variant: button.variant,
                      onPressed: button.onPressed,
                    ),
                    if (button != buttons.last) const SizedBox(height: 8),
                  ],
                ],
              ),
            ),
          ],
        ],
      );
    }

    return _AssignmentPrompt(
      label: 'Asignar silla',
      onTap: onAction,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.add_rounded, size: 18, color: scheme.primary),
          const SizedBox(width: 6),
          Text(
            'Asignar silla',
            style: theme.textTheme.labelLarge?.copyWith(
              color: scheme.primary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  String get _saddleName {
    const separator = ' - ';
    final idx = saddleLabel.indexOf(separator);
    if (idx == -1) return saddleLabel;
    return saddleLabel.substring(idx + separator.length);
  }
}

class _AssignmentPrompt extends StatelessWidget {
  const _AssignmentPrompt({
    required this.label,
    required this.child,
    this.onTap,
  });

  final String label;
  final Widget child;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final enabled = onTap != null;

    return Semantics(
      button: true,
      enabled: enabled,
      label: label,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(4),
          child: Opacity(
            opacity: enabled ? 1 : 0.55,
            child: CustomPaint(
              painter: _DashedRectPainter(
                color: scheme.outlineVariant,
                strokeWidth: 1,
                dashWidth: 6,
                gapWidth: 4,
              ),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                child: child,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _EquineThumb extends StatelessWidget {
  const _EquineThumb({this.image});

  final ImageProvider? image;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return ClipRRect(
      borderRadius: BorderRadius.circular(4),
      child: Container(
        width: 42,
        height: 42,
        color: scheme.surfaceContainerHigh,
        child: image != null
            ? Image(image: image!, fit: BoxFit.cover)
            : Icon(
                Symbols.chess_knight,
                size: 24,
                color: scheme.onSurfaceVariant,
              ),
      ),
    );
  }
}

class _InlineAction {
  const _InlineAction({
    required this.label,
    required this.icon,
    required this.variant,
    required this.onPressed,
  });

  final String label;
  final IconData icon;
  final AppButtonVariant variant;
  final VoidCallback? onPressed;
}

class _CompactActionButton extends StatelessWidget {
  const _CompactActionButton({
    required this.label,
    required this.icon,
    required this.variant,
    required this.onPressed,
  });

  final String label;
  final IconData icon;
  final AppButtonVariant variant;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;
    final enabled = onPressed != null;

    final Color bg;
    final Color fg;
    final BorderSide? side;

    if (variant == AppButtonVariant.danger) {
      bg = scheme.error.withValues(alpha: enabled ? 0.12 : 0.08);
      fg = scheme.error;
      side = BorderSide(color: scheme.error.withValues(alpha: 0.28));
    } else if (variant == AppButtonVariant.secondary) {
      bg = scheme.surfaceContainerLow;
      fg = scheme.onSurface;
      side = BorderSide(color: scheme.outlineVariant.withValues(alpha: 0.35));
    } else {
      bg = Colors.transparent;
      fg = scheme.onSurfaceVariant;
      side = null;
    }

    Widget button = Material(
      color: bg,
      borderRadius: tokens.radiusSm,
      child: InkWell(
        onTap: onPressed,
        borderRadius: tokens.radiusSm,
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Icon(icon, size: 16, color: fg),
        ),
      ),
    );

    if (side != null) {
      button = DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: tokens.radiusSm,
          border: Border.fromBorderSide(side),
        ),
        child: button,
      );
    }

    return Semantics(
      button: true,
      enabled: enabled,
      label: label,
      child: Tooltip(
        message: label,
        child: Opacity(opacity: enabled ? 1 : 0.55, child: button),
      ),
    );
  }
}

class _DashedRectPainter extends CustomPainter {
  final Color color;
  final double strokeWidth;
  final double dashWidth;
  final double gapWidth;

  const _DashedRectPainter({
    required this.color,
    this.strokeWidth = 1.0,
    this.dashWidth = 4.0,
    this.gapWidth = 3.0,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke;

    final rect = RRect.fromRectAndRadius(
      Rect.fromLTWH(0, 0, size.width, size.height),
      const Radius.circular(4),
    );

    final path = Path()..addRRect(rect);
    final dashed = Path();
    for (final metric in path.computeMetrics()) {
      double distance = 0.0;
      while (distance < metric.length) {
        final end = (distance + dashWidth).clamp(0.0, metric.length);
        dashed.addPath(metric.extractPath(distance, end), Offset.zero);
        distance += dashWidth + gapWidth;
      }
    }
    canvas.drawPath(dashed, paint);
  }

  @override
  bool shouldRepaint(covariant _DashedRectPainter oldDelegate) =>
      oldDelegate.color != color ||
      oldDelegate.strokeWidth != strokeWidth ||
      oldDelegate.dashWidth != dashWidth ||
      oldDelegate.gapWidth != gapWidth;
}

class _InlineValidationBanner extends StatelessWidget {
  const _InlineValidationBanner({required this.message, required this.state});

  final String message;
  final AppAssignmentCardState state;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final accent = state == AppAssignmentCardState.error
        ? scheme.error
        : scheme.tertiary;
    final icon = state == AppAssignmentCardState.error
        ? Icons.error_outline_rounded
        : Icons.warning_amber_rounded;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: accent.withValues(alpha: 0.32)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: accent),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: accent,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
