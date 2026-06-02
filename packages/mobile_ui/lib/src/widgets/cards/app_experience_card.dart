import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';

enum AppExperienceCardVariant { compact, commercial, operational }

class AppOperationalBadgeData {
  const AppOperationalBadgeData({
    required this.label,
    this.icon,
    this.tone = AppBadgeTone.neutral,
  });

  final String label;
  final IconData? icon;
  final AppBadgeTone tone;
}

class AppExperienceCardData {
  const AppExperienceCardData({
    required this.title,
    required this.description,
    required this.activityDurationLabel,
    required this.routeDurationLabel,
    required this.difficultyLabel,
    this.image,
    this.priceLabel,
    this.priceCaption,
    this.distanceLabel,
    this.terrainLabel,
    this.capacityLabel,
    this.inclusions = const [],
    this.badges = const [],
    this.scheduleLabel,
    this.availableSlotsLabel,
    this.stateLabel,
  });

  final String title;
  final String description;
  final ImageProvider? image;
  final String? priceLabel;
  final String? priceCaption;
  final String activityDurationLabel;
  final String routeDurationLabel;
  final String? distanceLabel;
  final String? terrainLabel;
  final String difficultyLabel;
  final String? capacityLabel;
  final List<String> inclusions;
  final List<AppOperationalBadgeData> badges;
  final String? scheduleLabel;
  final String? availableSlotsLabel;
  final String? stateLabel;
}

class AppExperienceCard extends StatelessWidget {
  const AppExperienceCard({
    super.key,
    required this.data,
    this.variant = AppExperienceCardVariant.commercial,
    this.primaryActionLabel,
    this.onTap,
    this.onPrimaryAction,
    this.enabled = true,
    this.selected = false,
  });

  final AppExperienceCardData data;
  final AppExperienceCardVariant variant;
  final String? primaryActionLabel;
  final VoidCallback? onTap;
  final VoidCallback? onPrimaryAction;
  final bool enabled;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    final compact = variant == AppExperienceCardVariant.compact;
    final operational = variant == AppExperienceCardVariant.operational;
    final showImage = data.image != null && !compact;
    final showInclusions = data.inclusions.isNotEmpty && !compact;

    final card = Container(
      decoration: BoxDecoration(
        color: selected
            ? scheme.surfaceContainerHighest
            : scheme.surfaceContainerHigh,
        borderRadius: tokens.radiusLg,
        border: Border.all(
          color: selected
              ? scheme.primary.withValues(alpha: 0.55)
              : scheme.outlineVariant.withValues(alpha: 0.26),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (showImage)
            ClipRRect(
              borderRadius: BorderRadius.only(
                topLeft: tokens.radiusLg.topLeft,
                topRight: tokens.radiusLg.topRight,
              ),
              child: Image(
                image: data.image!,
                width: double.infinity,
                height: 184,
                fit: BoxFit.cover,
              ),
            ),
          Padding(
            padding: EdgeInsets.all(compact ? 14 : 18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (data.badges.isNotEmpty) ...[
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: data.badges
                        .map(
                          (badge) => AppBadge(
                            label: badge.label,
                            icon: badge.icon,
                            tone: badge.tone,
                            uppercase: false,
                          ),
                        )
                        .toList(),
                  ),
                  const SizedBox(height: 12),
                ],
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            data.title.toUpperCase(),
                            maxLines: compact ? 2 : 3,
                            overflow: TextOverflow.ellipsis,
                            style: theme.textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w900,
                              height: 1.05,
                              color: scheme.onSurface,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            data.description,
                            maxLines: compact ? 2 : 4,
                            overflow: TextOverflow.ellipsis,
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: scheme.onSurfaceVariant,
                              height: 1.4,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (data.priceLabel != null && !operational) ...[
                      const SizedBox(width: 10),
                      _PriceSummary(
                        priceLabel: data.priceLabel!,
                        caption: data.priceCaption ?? 'Tarifa por persona',
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 14),
                Wrap(
                  spacing: 12,
                  runSpacing: 8,
                  children: [
                    _Meta(
                      icon: Icons.timelapse_rounded,
                      label: data.activityDurationLabel,
                    ),
                    _Meta(
                      icon: Icons.route_rounded,
                      label: data.routeDurationLabel,
                    ),
                    _Meta(
                      icon: Icons.terrain_rounded,
                      label: data.difficultyLabel,
                    ),
                    if (data.distanceLabel != null)
                      _Meta(
                        icon: Icons.straighten_rounded,
                        label: data.distanceLabel!,
                      ),
                    if (data.terrainLabel != null)
                      _Meta(icon: Icons.map_rounded, label: data.terrainLabel!),
                    if (data.capacityLabel != null)
                      _Meta(
                        icon: Icons.groups_rounded,
                        label: data.capacityLabel!,
                      ),
                    if (operational && data.scheduleLabel != null)
                      _Meta(
                        icon: Icons.schedule_rounded,
                        label: data.scheduleLabel!,
                      ),
                    if (operational && data.availableSlotsLabel != null)
                      _Meta(
                        icon: Icons.event_seat_rounded,
                        label: data.availableSlotsLabel!,
                      ),
                    if (operational && data.stateLabel != null)
                      _Meta(
                        icon: Icons.info_outline_rounded,
                        label: data.stateLabel!,
                      ),
                  ],
                ),
                if (showInclusions) ...[
                  const SizedBox(height: 14),
                  Text(
                    'INCLUYE',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: data.inclusions
                        .map(
                          (item) => AppBadge(
                            label: item,
                            tone: AppBadgeTone.ghost,
                            uppercase: false,
                          ),
                        )
                        .toList(),
                  ),
                ],
                if (onPrimaryAction != null) ...[
                  const SizedBox(height: 16),
                  AppButton(
                    label: primaryActionLabel ?? _defaultActionLabel(),
                    icon: _defaultActionIcon(),
                    expanded: true,
                    onPressed: enabled ? onPrimaryAction : null,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );

    return Opacity(
      opacity: enabled ? 1 : 0.55,
      child: Material(
        color: Colors.transparent,
        borderRadius: tokens.radiusLg,
        child: InkWell(
          borderRadius: tokens.radiusLg,
          onTap: enabled ? onTap : null,
          child: card,
        ),
      ),
    );
  }

  String _defaultActionLabel() {
    switch (variant) {
      case AppExperienceCardVariant.compact:
        return 'Ver detalle';
      case AppExperienceCardVariant.commercial:
        return 'Cotizar';
      case AppExperienceCardVariant.operational:
        return 'Asociar con reserva';
    }
  }

  IconData _defaultActionIcon() {
    switch (variant) {
      case AppExperienceCardVariant.compact:
        return Icons.arrow_forward_rounded;
      case AppExperienceCardVariant.commercial:
        return Icons.request_quote_rounded;
      case AppExperienceCardVariant.operational:
        return Icons.link_rounded;
    }
  }
}

class _Meta extends StatelessWidget {
  const _Meta({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: scheme.onSurfaceVariant),
        const SizedBox(width: 6),
        Text(
          label.toUpperCase(),
          style: theme.textTheme.labelMedium?.copyWith(
            color: scheme.onSurface,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.4,
          ),
        ),
      ],
    );
  }
}

class _PriceSummary extends StatelessWidget {
  const _PriceSummary({required this.priceLabel, required this.caption});

  final String priceLabel;
  final String caption;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          priceLabel,
          style: theme.textTheme.titleMedium?.copyWith(
            color: scheme.onSurface,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          caption.toUpperCase(),
          textAlign: TextAlign.right,
          style: theme.textTheme.labelSmall?.copyWith(
            color: scheme.onSurfaceVariant,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.6,
          ),
        ),
      ],
    );
  }
}
