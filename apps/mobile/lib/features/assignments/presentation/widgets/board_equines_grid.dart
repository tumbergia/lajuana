import 'package:flutter/material.dart';

import '../../domain/models/assignment_board.dart';

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

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: equines.map((eq) {
        final isAvailable = eq.isAvailable;
        return SizedBox(
          width: 140,
          child: Container(
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
                      Icons.pets_rounded,
                      size: 16,
                      color: isAvailable
                          ? const Color(0xFF2E7D32)
                          : scheme.onSurfaceVariant,
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        eq.name,
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
                if (eq.blockReason != null) ...[
                  const SizedBox(height: 6),
                  Text(
                    eq.blockReason!,
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: scheme.error,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
                const SizedBox(height: 4),
                Text(
                  eq.maxRiderWeightKg != null
                      ? 'Máx. ${eq.maxRiderWeightKg!.toStringAsFixed(0)} kg'
                      : 'Sin límite de peso',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: eq.maxRiderWeightKg != null
                        ? scheme.onSurfaceVariant
                        : scheme.onSurfaceVariant.withValues(alpha: 0.45),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
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
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(color: scheme.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}
