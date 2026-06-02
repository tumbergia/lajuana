import 'package:flutter/material.dart';

import '../../../../app/theme/theme_extensions.dart';
import '../../../../app/widgets/app_badge.dart';
import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_scaffold.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/cards/app_assignment_card.dart';
import '../../domain/models/assignment_board.dart';
import '../../domain/models/assignment_status.dart';
import '../controllers/assignment_board_controller.dart';

/// Pantalla de tablero de asignaciones para una reserva.
///
/// Muestra el resumen de asignaciones, lista de participantes con su
/// estado de asignación, equinos y sillas disponibles.
class AssignmentBoardScreen extends StatefulWidget {
  final AssignmentBoardController controller;
  final String reservationId;

  const AssignmentBoardScreen({
    super.key,
    required this.controller,
    required this.reservationId,
  });

  @override
  State<AssignmentBoardScreen> createState() => _AssignmentBoardScreenState();
}

class _AssignmentBoardScreenState extends State<AssignmentBoardScreen> {
  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onStateChanged);
    widget.controller.load(
      reservationId: widget.reservationId,
    );
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onStateChanged);
    super.dispose();
  }

  void _onStateChanged() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final ctrl = widget.controller;

    return AppScaffold(
      appBar: AppBar(
        title: const Text('Asignaciones'),
        actions: [
          if (ctrl.state == BoardLoadState.loaded)
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              onPressed: ctrl.refresh,
              tooltip: 'Actualizar',
            ),
        ],
      ),
      child: _buildBody(ctrl),
    );
  }

  Widget _buildBody(AssignmentBoardController ctrl) {
    switch (ctrl.state) {
      case BoardLoadState.initial:
      case BoardLoadState.loading:
        return const AppCenteredLoader();
      case BoardLoadState.error:
        return _ErrorState(
          message: ctrl.error ?? 'Error al cargar el tablero',
          onRetry: ctrl.refresh,
        );
      case BoardLoadState.loaded:
        final board = ctrl.board;
        if (board == null) {
          return const _ErrorState(message: 'No hay datos disponibles');
        }
        return _BoardContent(board: board);
    }
  }
}

// ── Board content ──

class _BoardContent extends StatelessWidget {
  final AssignmentBoard board;

  const _BoardContent({required this.board});

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Summary stats bar ──
        _SummaryBar(summary: board.summary),

        const SizedBox(height: 24),

        // ── Participants section ──
        AppSectionHeader(
          title: 'Participantes',
          subtitle: '${board.participants.length} registrados',
          variant: AppSectionHeaderVariant.compact,
          trailing: _AssignmentStatusBadge(status: _computeBoardStatus()),
        ),

        const SizedBox(height: 16),

        if (board.participants.isEmpty)
          _EmptyState(message: 'No hay participantes registrados')
        else
          ...board.participants.map((p) => Padding(
                padding: EdgeInsets.only(
                  bottom: tokens.spaceMd,
                ),
                child: _ParticipantAssignmentCard(
                  participant: p,
                  availableEquines: board.availableEquines,
                  availableSaddles: board.availableSaddles,
                ),
              )),

        const SizedBox(height: 24),

        // ── Available equines section ──
        AppSectionHeader(
          title: 'Equinos disponibles',
          subtitle:
              '${board.availableEquines.where((e) => e.isAvailable).length} disponibles',
          variant: AppSectionHeaderVariant.compact,
        ),
        const SizedBox(height: 12),
        _AvailableEquinesGrid(equines: board.availableEquines),

        const SizedBox(height: 24),

        // ── Available saddles section ──
        AppSectionHeader(
          title: 'Sillas disponibles',
          subtitle:
              '${board.availableSaddles.where((s) => s.isAvailable).length} disponibles',
          variant: AppSectionHeaderVariant.compact,
        ),
        const SizedBox(height: 12),
        _AvailableSaddlesGrid(saddles: board.availableSaddles),
      ],
    );
  }

  String _computeBoardStatus() {
    final s = board.summary;
    if (s.blockingTotal > 0) return 'bloqueado';
    if (s.assignedTotal >= s.participantsTotal) return 'completo';
    if (s.assignedTotal > 0) return 'parcial';
    return 'pendiente';
  }
}

// ── Summary stats bar ──

class _SummaryBar extends StatelessWidget {
  final BoardSummary summary;

  const _SummaryBar({required this.summary});

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
            icon: Icons.people_outline_rounded,
            value: '${summary.participantsTotal}',
            label: 'Total',
            color: scheme.onSurface,
          ),
          _StatDivider(color: scheme.outlineVariant),
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
          Text(
            label.toUpperCase(),
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.5,
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

// ── Assignment status badge ──

class _AssignmentStatusBadge extends StatelessWidget {
  final String status;

  const _AssignmentStatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    late final AppBadgeTone tone;
    late final IconData icon;
    late final String label;

    switch (status) {
      case 'completo':
        tone = AppBadgeTone.success;
        icon = Icons.check_circle_rounded;
        label = 'Completo';
      case 'parcial':
        tone = AppBadgeTone.warning;
        icon = Icons.adjust_rounded;
        label = 'Parcial';
      case 'pendiente':
        tone = AppBadgeTone.neutral;
        icon = Icons.schedule_rounded;
        label = 'Pendiente';
      case 'bloqueado':
        tone = AppBadgeTone.danger;
        icon = Icons.error_outline_rounded;
        label = 'Bloqueado';
      default:
        tone = AppBadgeTone.neutral;
        icon = Icons.help_outline_rounded;
        label = status;
    }

    return AppBadge(
      label: label,
      tone: tone,
      icon: icon,
      size: AppBadgeSize.md,
    );
  }
}

// ── Participant assignment card ──

class _ParticipantAssignmentCard extends StatelessWidget {
  final BoardParticipant participant;
  final List<AvailableEquine> availableEquines;
  final List<AvailableSaddle> availableSaddles;

  const _ParticipantAssignmentCard({
    required this.participant,
    required this.availableEquines,
    required this.availableSaddles,
  });

  @override
  Widget build(BuildContext context) {
    final assignment = participant.assignment;
    final hasBlockingIssues = participant.blockingReasons.isNotEmpty;

    // Resolver estado de la card
    final AppAssignmentCardState cardState;
    final String? validationMessage;

    if (assignment == null) {
      // Sin asignación
      if (hasBlockingIssues) {
        cardState = AppAssignmentCardState.error;
        validationMessage = participant.blockingReasons.join('\n');
      } else {
        cardState = AppAssignmentCardState.warning;
        validationMessage = 'Pendiente de asignación';
      }
    } else {
      // Con asignación
      if (assignment.warnings.isNotEmpty) {
        cardState = AppAssignmentCardState.warning;
        validationMessage = assignment.warnings.join('\n');
      } else if (assignment.status == AssignmentStatus.final_) {
        cardState = AppAssignmentCardState.ok;
        validationMessage = null;
      } else if (assignment.status == AssignmentStatus.confirmed) {
        cardState = AppAssignmentCardState.ok;
        validationMessage = null;
      } else {
        cardState = AppAssignmentCardState.warning;
        validationMessage = 'Estado: ${assignment.status?.name ?? "desconocido"}';
      }
    }

    // Calcular load ratio
    final participantWeight = participant.weightKg ?? 0;
    final equineMaxWeight = () {
      if (assignment?.equineId == null) return null;
      final eq = availableEquines.cast<AvailableEquine?>().firstWhere(
            (e) => e?.id == assignment!.equineId,
            orElse: () => null,
          );
      return eq?.maxRiderWeightKg;
    }();
    final loadRatio = (equineMaxWeight != null && equineMaxWeight > 0)
        ? (participantWeight / equineMaxWeight)
        : 0.0;

    return AppAssignmentCard(
      startTimeLabel: '—',
      participant: AppAssignmentParticipantData(
        name: participant.fullName,
        weightLabel: '${participant.weightKg?.toStringAsFixed(0) ?? "?"} kg',
        experienceLabel: _experienceLabel(participant.experienceLevel),
        ageLabel: participant.ageYears != null
            ? '${participant.ageYears} años'
            : null,
      ),
      equine: AppAssignmentEquineData(
        name: assignment?.equineName ?? 'Sin asignar',
        capacityLabel: equineMaxWeight != null
            ? 'Máx. ${equineMaxWeight.toStringAsFixed(0)} kg'
            : 'Sin límite de peso',
        statusLabel: assignment?.status?.name,
      ),
      saddleLabel: assignment?.saddleLabel ?? '—',
      loadRatio: loadRatio,
      state: cardState,
      validationMessage: validationMessage,
      safetyFlags: assignment?.warnings ?? [],
      onChangeEquine: null, // TODO: implementar selector
      onChangeSaddle: null, // TODO: implementar selector
    );
  }

  String? _experienceLabel(String? level) {
    if (level == null) return null;
    switch (level) {
      case 'basic':
        return 'Básico';
      case 'intermediate':
        return 'Intermedio';
      case 'advanced':
        return 'Avanzado';
      default:
        return level;
    }
  }
}

// ── Available equines grid ──

class _AvailableEquinesGrid extends StatelessWidget {
  final List<AvailableEquine> equines;

  const _AvailableEquinesGrid({required this.equines});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    if (equines.isEmpty) {
      return _EmptyState(message: 'No hay equinos registrados');
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
                if (eq.maxRiderWeightKg != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    'Máx. ${eq.maxRiderWeightKg!.toStringAsFixed(0)} kg',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ── Available saddles grid ──

class _AvailableSaddlesGrid extends StatelessWidget {
  final List<AvailableSaddle> saddles;

  const _AvailableSaddlesGrid({required this.saddles});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    if (saddles.isEmpty) {
      return _EmptyState(message: 'No hay sillas registradas');
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: saddles.map((saddle) {
        final isAvailable = saddle.isAvailable;
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
                if (saddle.blockReason != null) ...[
                  const SizedBox(height: 6),
                  Text(
                    saddle.blockReason!,
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: scheme.error,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ── Empty state ──

class _EmptyState extends StatelessWidget {
  final String message;

  const _EmptyState({required this.message});

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
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: scheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Error state ──

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const _ErrorState({required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline_rounded,
              size: 48,
              color: scheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              AppButton(
                label: 'Reintentar',
                icon: Icons.refresh_rounded,
                onPressed: onRetry,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
