import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_domain/src/assignments/assignment_board.dart';

import 'board_block_reason.dart';
import 'board_grid_layout.dart';

/// Grid de equinos disponibles/no disponibles.
class BoardEquinesGrid extends StatelessWidget {
  final List<AvailableEquine> equines;

  const BoardEquinesGrid({required this.equines});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    if (equines.isEmpty) {
      return _BoardEmptyState(message: 'No hay equinos registrados');
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        const spacing = 8.0;
        final maxWidth = constraints.maxWidth;
        final layout = BoardGridLayout.forWidth(
          maxWidth: maxWidth,
          itemCount: equines.length,
          spacing: spacing,
        );

        return Wrap(
          spacing: spacing,
          runSpacing: spacing,
          children: [
            for (var i = 0; i < equines.length; i++)
              SizedBox(
                width: layout.cardWidthFor(i, equines.length, maxWidth),
                child: _EquineCard(
                  equine: equines[i],
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

class _EquineCard extends StatelessWidget {
  const _EquineCard({
    required this.equine,
    required this.theme,
    required this.scheme,
  });

  final AvailableEquine equine;
  final ThemeData theme;
  final ColorScheme scheme;

  @override
  Widget build(BuildContext context) {
    final isAvailable = equine.isAvailable;
    final blockReasonLabel = displayBoardBlockReason(equine.blockReason);

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
                Symbols.chess_knight,
                size: 16,
                color: isAvailable
                    ? const Color(0xFF2E7D32)
                    : scheme.onSurfaceVariant,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  equine.name,
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
          const SizedBox(height: 4),
          Text(
            equine.maxRiderWeightKg != null
                ? 'Máx. ${equine.maxRiderWeightKg!.toStringAsFixed(0)} kg'
                : 'Sin límite de peso',
            style: theme.textTheme.labelSmall?.copyWith(
              color: equine.maxRiderWeightKg != null
                  ? scheme.onSurfaceVariant
                  : scheme.onSurfaceVariant.withValues(alpha: 0.45),
              fontWeight: FontWeight.w500,
            ),
          ),
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
