import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';

enum AppLogbookEntryState { active, completed, neutral, warning, error }

class AppLogbookTimelineEntry {
  const AppLogbookTimelineEntry({
    required this.title,
    required this.dateLabel,
    required this.reservationLabel,
    required this.guideLabel,
    required this.durationLabel,
    this.state = AppLogbookEntryState.neutral,
    this.badge,
    this.observations,
    this.photos = const [],
    this.highlightedContent,
    this.footer,
    this.onTap,
    this.onEdit,
    this.onAddPhoto,
  });

  final String title;
  final String dateLabel;
  final String reservationLabel;
  final String guideLabel;
  final String durationLabel;
  final AppLogbookEntryState state;
  final AppBadge? badge;
  final String? observations;
  final List<ImageProvider> photos;
  final Widget? highlightedContent;
  final Widget? footer;
  final VoidCallback? onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onAddPhoto;
}

class AppLogbookTimeline extends StatelessWidget {
  const AppLogbookTimeline({
    super.key,
    required this.entries,
    this.lineLeft = 12,
    this.itemSpacing = 24,
  });

  final List<AppLogbookTimelineEntry> entries;
  final double lineLeft;
  final double itemSpacing;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Stack(
      children: [
        Positioned(
          left: lineLeft - 0.75,
          top: 0,
          bottom: 0,
          child: Container(width: 1.5, color: scheme.outlineVariant),
        ),
        Column(
          children: [
            for (var index = 0; index < entries.length; index++) ...[
              _LogbookTimelineItem(entry: entries[index], lineLeft: lineLeft),
              if (index != entries.length - 1) SizedBox(height: itemSpacing),
            ],
          ],
        ),
      ],
    );
  }
}

class _LogbookTimelineItem extends StatelessWidget {
  const _LogbookTimelineItem({required this.entry, required this.lineLeft});

  final AppLogbookTimelineEntry entry;
  final double lineLeft;

  @override
  Widget build(BuildContext context) {
    final nodeColor = _nodeColor(context);
    final isDimmed = entry.state == AppLogbookEntryState.completed;

    return Opacity(
      opacity: isDimmed ? 0.82 : 1,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: lineLeft * 2 + 8,
            child: Align(
              alignment: Alignment.topLeft,
              child: Transform.translate(
                offset: Offset(lineLeft - 4, 8),
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: nodeColor,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(child: AppLogbookEntryCard(entry: entry)),
        ],
      ),
    );
  }

  Color _nodeColor(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    switch (entry.state) {
      case AppLogbookEntryState.active:
        return scheme.primary;
      case AppLogbookEntryState.completed:
      case AppLogbookEntryState.neutral:
        return scheme.outlineVariant;
      case AppLogbookEntryState.warning:
        return scheme.tertiary;
      case AppLogbookEntryState.error:
        return scheme.error;
    }
  }
}

class AppLogbookEntryCard extends StatelessWidget {
  const AppLogbookEntryCard({super.key, required this.entry});

  final AppLogbookTimelineEntry entry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    return Material(
      color: scheme.surfaceContainerHighest,
      borderRadius: tokens.radiusMd,
      child: InkWell(
        borderRadius: tokens.radiusMd,
        onTap: entry.onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          entry.dateLabel.toUpperCase(),
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: scheme.onSurfaceVariant,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.8,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          entry.title.toUpperCase(),
                          style: theme.textTheme.titleMedium?.copyWith(
                            color: scheme.onSurface,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (entry.badge != null) entry.badge!,
                ],
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: _InfoBox(
                      label: 'Reserva',
                      value: entry.reservationLabel,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _InfoBox(label: 'Guia', value: entry.guideLabel),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _InfoBox(
                      label: 'Duracion',
                      value: entry.durationLabel,
                    ),
                  ),
                ],
              ),
              if (entry.highlightedContent != null) ...[
                const SizedBox(height: 14),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: scheme.surfaceContainerLow,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: entry.highlightedContent!,
                ),
              ],
              if (entry.observations != null) ...[
                const SizedBox(height: 14),
                Text(
                  'OBSERVACIONES',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.8,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  entry.observations!,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                    height: 1.45,
                  ),
                ),
              ],
              if (entry.photos.isNotEmpty || entry.onAddPhoto != null) ...[
                const SizedBox(height: 14),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final photo in entry.photos.take(6))
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: Image(
                          image: photo,
                          width: 58,
                          height: 58,
                          fit: BoxFit.cover,
                        ),
                      ),
                    if (entry.onAddPhoto != null)
                      Material(
                        color: scheme.surfaceContainerLow,
                        borderRadius: BorderRadius.circular(4),
                        child: InkWell(
                          onTap: entry.onAddPhoto,
                          borderRadius: BorderRadius.circular(4),
                          child: SizedBox(
                            width: 58,
                            height: 58,
                            child: Icon(
                              Icons.add_a_photo_outlined,
                              color: scheme.onSurfaceVariant,
                              size: 18,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ],
              if (entry.footer != null) ...[
                const SizedBox(height: 14),
                entry.footer!,
              ],
              if (entry.onEdit != null) ...[
                const SizedBox(height: 14),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton.icon(
                    onPressed: entry.onEdit,
                    icon: const Icon(Icons.edit_rounded, size: 14),
                    label: const Text('EDITAR ENTRADA'),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoBox extends StatelessWidget {
  const _InfoBox({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.labelSmall?.copyWith(
              color: scheme.onSurfaceVariant,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.7,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.labelMedium?.copyWith(
              color: scheme.onSurface,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
