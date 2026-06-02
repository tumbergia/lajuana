import 'package:flutter/material.dart';

import '../../domain/models/assignment_board.dart';

/// Barra de resumen con conteo de asignados/pendientes/bloqueados.
class BoardSummaryBar extends StatelessWidget {
  final BoardSummary summary;

  const BoardSummaryBar({required this.summary});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          _StatItem(
            icon: Icons.check_circle_outline_rounded,
            value: '${summary.assignedTotal}',
            label: 'Asignados',
            color: const Color(0xFF2E7D32),
          ),
          _StatDivider(color: scheme.outlineVariant),
          _StatItem(
            icon: Icons.schedule_rounded,
            value: '${summary.pendingTotal}',
            label: 'Pendientes',
            color: const Color(0xFFF9A825),
          ),
          _StatDivider(color: scheme.outlineVariant),
          _StatItem(
            icon: Icons.block_rounded,
            value: '${summary.blockingTotal}',
            label: 'Bloqueados',
            color: const Color(0xFFB3261E),
          ),
        ],
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;

  const _StatItem({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Expanded(
      child: Column(
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(height: 4),
          Text(
            value,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w900,
              color: color,
            ),
          ),
          const SizedBox(height: 6),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              label.toUpperCase(),
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatDivider extends StatelessWidget {
  final Color color;

  const _StatDivider({required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 1,
      height: 48,
      color: color.withValues(alpha: 0.3),
      margin: const EdgeInsets.symmetric(horizontal: 8),
    );
  }
}
