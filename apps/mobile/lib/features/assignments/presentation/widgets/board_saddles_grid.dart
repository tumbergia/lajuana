import 'package:flutter/material.dart';

import 'package:mobile_domain/src/assignments/assignment_board.dart';

import 'board_block_reason.dart';
import 'board_grid_layout.dart';

/// Grid de sillas disponibles/no disponibles.
class BoardSaddlesGrid extends StatelessWidget {
  final List<AvailableSaddle> saddles;

  const BoardSaddlesGrid({required this.saddles});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    if (saddles.isEmpty) {
      return _BoardEmptyState(message: 'No hay sillas registradas');
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        const spacing = 8.0;
        final maxWidth = constraints.maxWidth;
        final layout = BoardGridLayout.forWidth(
          maxWidth: maxWidth,
          itemCount: saddles.length,
          spacing: spacing,
        );

        return Wrap(
          spacing: spacing,
          runSpacing: spacing,
          children: [
            for (var i = 0; i < saddles.length; i++)
              SizedBox(
                width: layout.cardWidthFor(i, saddles.length, maxWidth),
                child: _SaddleCard(
                  saddle: saddles[i],
                  theme: theme,
                  scheme: scheme,
                ),
              ),
          ],
        );
      },
    );
  }
}

class _SaddleCard extends StatelessWidget {
  const _SaddleCard({
    required this.saddle,
    required this.theme,
    required this.scheme,
  });

  final AvailableSaddle saddle;
  final ThemeData theme;
  final ColorScheme scheme;

  @override
  Widget build(BuildContext context) {
    final isAvailable = saddle.isAvailable;
    final blockReasonLabel = displayBoardBlockReason(saddle.blockReason);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isAvailable
            ? scheme.surfaceContainerLow
            : scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(
          color: isAvailable
              ? scheme.outlineVariant.withValues(alpha: 0.3)
              : scheme.error.withValues(alpha: 0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.airline_seat_recline_normal_rounded,
                size: 16,
                color: isAvailable
                    ? const Color(0xFF2E7D32)
                    : scheme.onSurfaceVariant,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  saddle.code,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: isAvailable
                        ? scheme.onSurface
                        : scheme.onSurfaceVariant,
                  ),
                ),
              ),
            ],
          ),
          if (saddle.name != null) ...[
            const SizedBox(height: 4),
            Text(
              saddle.name!,
              style: theme.textTheme.labelSmall?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
          ],
          if (blockReasonLabel != null) ...[
            const SizedBox(height: 6),
            Text(
              blockReasonLabel,
              style: theme.textTheme.labelSmall?.copyWith(
                color: scheme.error,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _BoardEmptyState extends StatelessWidget {
  final String message;

  const _BoardEmptyState({required this.message});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        children: [
          Icon(
            Icons.inbox_outlined,
            size: 40,
            color: scheme.onSurfaceVariant.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 12),
          Text(
            message,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}
