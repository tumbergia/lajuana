import 'package:flutter/material.dart';

import '../app_badge.dart';
import '../app_button.dart';
import '../../theme/theme_extensions.dart';

enum AppAssignmentCardState { ok, warning, error }

class AppAssignmentParticipantData {
  const AppAssignmentParticipantData({
    required this.name,
    required this.weightLabel,
    this.experienceLabel,
    this.ageLabel,
  });

  final String name;
  final String weightLabel;
  final String? experienceLabel;
  final String? ageLabel;
}

class AppAssignmentEquineData {
  const AppAssignmentEquineData({
    required this.name,
    required this.capacityLabel,
    this.statusLabel,
    this.image,
  });

  final String name;
  final String capacityLabel;
  final String? statusLabel;
  final ImageProvider? image;
}

class AppAssignmentCard extends StatelessWidget {
  const AppAssignmentCard({
    super.key,
    required this.startTimeLabel,
    required this.participant,
    required this.equine,
    required this.saddleLabel,
    required this.loadRatio,
    this.reservationLabel,
    this.validationMessage,
    this.state = AppAssignmentCardState.ok,
    this.onTap,
    this.onChangeEquine,
    this.onChangeSaddle,
    this.safetyFlags = const [],
  });

  final String startTimeLabel;
  final AppAssignmentParticipantData participant;
  final AppAssignmentEquineData equine;
  final String saddleLabel;
  final double loadRatio;
  final String? reservationLabel;
  final String? validationMessage;
  final AppAssignmentCardState state;
  final VoidCallback? onTap;
  final VoidCallback? onChangeEquine;
  final VoidCallback? onChangeSaddle;
  final List<String> safetyFlags;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;
    final accent = _accentForState(scheme);

    final content = Container(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: tokens.radiusLg,
        border: Border.all(
          color: accent.withValues(alpha: 0.25),
          width: 0.5,
        ),
      ),
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
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
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ── Header row: reservation badge + time ──
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: reservationLabel == null
                              ? const SizedBox.shrink()
                              : AppBadge(
                                  label: reservationLabel!,
                                  icon: Icons.confirmation_number_outlined,
                                  uppercase: false,
                                ),
                        ),
                        _HeaderInfo(
                          title: 'Hora',
                          value: startTimeLabel,
                          icon: Icons.schedule_rounded,
                        ),
                      ],
                    ),
                    const SizedBox(height: 18),

                    // ── Participant block ──
                    _EntityBox(
                      label: 'Participante',
                      title: participant.name,
                      subtitle: participant.weightLabel,
                      accent: accent,
                      icon: Icons.person_outline_rounded,
                      tags: [
                        if (participant.experienceLabel != null)
                          participant.experienceLabel!,
                        if (participant.ageLabel != null) participant.ageLabel!,
                      ],
                    ),

                    // ── Safety flags ──
                    if (safetyFlags.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: safetyFlags.map((flag) {
                          final isChild = flag.contains('child');
                          final isSenior = flag.contains('senior');
                          return AppBadge(
                            label: isChild
                                ? 'Menor de edad'
                                : isSenior
                                    ? 'Adulto mayor'
                                    : flag,
                            tone: AppBadgeTone.warning,
                            icon: isChild
                                ? Icons.child_care_outlined
                                : isSenior
                                    ? Icons.elderly_outlined
                                    : Icons.warning_amber_rounded,
                            uppercase: false,
                          );
                        }).toList(),
                      ),
                    ],

                    const SizedBox(height: 12),

                    // ── Connector arrow ──
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Expanded(
                          child: Divider(
                            color: accent.withValues(alpha: 0.45),
                            height: 1,
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          child: Icon(
                            Icons.arrow_downward_rounded,
                            color: accent,
                            size: 18,
                          ),
                        ),
                        Expanded(
                          child: Divider(
                            color: accent.withValues(alpha: 0.45),
                            height: 1,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),

                    // ── Equine block ──
                    _EntityBox(
                      label: 'Equino',
                      title: equine.name,
                      subtitle: equine.capacityLabel,
                      accent: accent,
                      icon: Icons.pets_rounded,
                      image: equine.image,
                      tags: [
                        if (equine.statusLabel != null) equine.statusLabel!,
                      ],
                    ),

                    // ── Validation warnings ──
                    if (validationMessage != null) ...[
                      const SizedBox(height: 14),
                      _ValidationBanner(
                        message: validationMessage!,
                        state: state,
                      ),
                    ],

                    const SizedBox(height: 16),
                    Divider(
                      color: scheme.outlineVariant.withValues(alpha: 0.35),
                    ),
                    const SizedBox(height: 14),

                    // ── Saddle block ──
                    Row(
                      children: [
                        Icon(
                          Icons.airline_seat_recline_normal_rounded,
                          size: 18,
                          color: scheme.onSurfaceVariant,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: _HeaderInfo(
                            title: state == AppAssignmentCardState.ok
                                ? 'Silla asignada'
                                : 'Silla recomendada',
                            value: saddleLabel,
                          ),
                        ),
                      ],
                    ),
                    if (onChangeSaddle != null) ...[
                      const SizedBox(height: 10),
                      AppButton(
                        label: 'Cambiar silla',
                        variant: AppButtonVariant.ghost,
                        icon: Icons.swap_horiz_rounded,
                        onPressed: onChangeSaddle,
                      ),
                    ],

                    const SizedBox(height: 16),

                    // ── Load ratio ──
                    Row(
                      children: [
                        Icon(
                          Icons.speed_rounded,
                          size: 16,
                          color: accent,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'CARGA',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: scheme.onSurfaceVariant,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.9,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(999),
                      child: LinearProgressIndicator(
                        value: loadRatio.clamp(0.0, 1.0),
                        minHeight: 6,
                        backgroundColor: scheme.surfaceContainerLow,
                        valueColor: AlwaysStoppedAnimation<Color>(accent),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '${(loadRatio * 100).round()}% DE LA CAPACIDAD',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: state == AppAssignmentCardState.ok
                            ? scheme.onSurface
                            : accent,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 0.5,
                      ),
                    ),

                    // ── Change equine button ──
                    if (onChangeEquine != null) ...[
                      const SizedBox(height: 16),
                      AppButton(
                        label: 'Cambiar equino',
                        icon: Icons.compare_arrows_rounded,
                        variant: AppButtonVariant.secondary,
                        expanded: true,
                        onPressed: onChangeEquine,
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );

    return Material(
      color: Colors.transparent,
      borderRadius: tokens.radiusLg,
      child: InkWell(
        onTap: onTap,
        borderRadius: tokens.radiusLg,
        child: content,
      ),
    );
  }

  Color _accentForState(ColorScheme scheme) {
    switch (state) {
      case AppAssignmentCardState.ok:
        return scheme.primary;
      case AppAssignmentCardState.warning:
        return scheme.tertiary;
      case AppAssignmentCardState.error:
        return scheme.error;
    }
  }
}

// ── Header info tile ──

class _HeaderInfo extends StatelessWidget {
  const _HeaderInfo({
    required this.title,
    required this.value,
    this.icon,
  });

  final String title;
  final String value;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(icon, size: 13, color: scheme.onSurfaceVariant),
              const SizedBox(width: 4),
            ],
            Text(
              title.toUpperCase(),
              style: theme.textTheme.labelSmall?.copyWith(
                color: scheme.onSurfaceVariant,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.8,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: theme.textTheme.titleMedium?.copyWith(
            color: scheme.onSurface,
            fontWeight: FontWeight.w900,
          ),
        ),
      ],
    );
  }
}

// ── Entity box (participant / equine) ──

class _EntityBox extends StatelessWidget {
  const _EntityBox({
    required this.label,
    required this.title,
    required this.subtitle,
    required this.accent,
    required this.icon,
    this.tags = const [],
    this.image,
  });

  final String label;
  final String title;
  final String subtitle;
  final Color accent;
  final IconData icon;
  final List<String> tags;
  final ImageProvider? image;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(6),
        border: Border(left: BorderSide(color: accent, width: 2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 14, color: accent),
              const SizedBox(width: 6),
              Text(
                label.toUpperCase(),
                style: theme.textTheme.labelSmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              if (image != null) ...[
                ClipRRect(
                  borderRadius: BorderRadius.circular(3),
                  child: Image(
                    image: image!,
                    width: 42,
                    height: 42,
                    fit: BoxFit.cover,
                  ),
                ),
                const SizedBox(width: 10),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.titleSmall?.copyWith(
                        color: scheme.onSurface,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle.toUpperCase(),
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (tags.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: tags
                  .map(
                    (tag) => AppBadge(
                      label: tag,
                      tone: AppBadgeTone.neutral,
                      uppercase: false,
                    ),
                  )
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Validation banner ──

class _ValidationBanner extends StatelessWidget {
  const _ValidationBanner({required this.message, required this.state});

  final String message;
  final AppAssignmentCardState state;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isError = state == AppAssignmentCardState.error;
    final accent = isError ? scheme.error : scheme.tertiary;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.12),
        border: Border.all(color: accent.withValues(alpha: 0.4)),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            isError ? Icons.error_outline_rounded : Icons.warning_amber_rounded,
            color: accent,
            size: 18,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: accent,
                fontWeight: FontWeight.w700,
                height: 1.3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
