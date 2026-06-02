import 'dart:convert';

import 'package:flutter/material.dart';

import '../../../../app/theme/theme_extensions.dart';
import '../../../../app/widgets/app_confirm_dialog.dart';
import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_scaffold.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_status_banner.dart';
import '../../../../app/widgets/cards/app_assignment_card.dart';
import '../../../../app/widgets/cards/app_assignment_list_item.dart';
import '../../domain/models/assignment_board.dart';
import '../../domain/models/assignment_status.dart';
import '../controllers/assignment_board_controller.dart';

/// Pantalla de tablero de asignaciones para una reserva.
///
/// Muestra el resumen de asignaciones, lista de participantes con su
/// estado de asignación, equinos y sillas disponibles.
///
/// [isAdmin] controla visibilidad de acciones de asignación.
/// [isOnline] controla si las acciones de escritura están habilitadas.
class AssignmentBoardScreen extends StatefulWidget {
  final AssignmentBoardController controller;
  final String reservationId;
  final bool isAdmin;
  final bool isOnline;

  const AssignmentBoardScreen({
    super.key,
    required this.controller,
    required this.reservationId,
    this.isAdmin = false,
    this.isOnline = true,
  });

  @override
  State<AssignmentBoardScreen> createState() => _AssignmentBoardScreenState();
}

class _AssignmentBoardScreenState extends State<AssignmentBoardScreen> {
  final _observationController = TextEditingController();

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onStateChanged);
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onStateChanged);
    _observationController.dispose();
    super.dispose();
  }

  void _onStateChanged() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final ctrl = widget.controller;

    return AppScaffold(child: _buildBody(ctrl));
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
      case BoardLoadState.offlineFromCache:
      case BoardLoadState.loaded:
        final board = ctrl.board;
        if (board == null) {
          return const _ErrorState(message: 'No hay datos disponibles');
        }
        return SingleChildScrollView(
          child: Column(
            children: [
              if (ctrl.isOffline)
                AppStatusBanner(
                  title: 'Datos almacenados',
                  message: 'Sin conexión — mostrando última vista guardada.',
                  tone: AppStatusBannerTone.warning,
                  icon: Icons.wifi_off_rounded,
                  badgeLabel: 'Offline',
                ),
              _BoardContent(
                board: board,
                ctrl: ctrl,
                isAdmin: widget.isAdmin,
                isOnline: widget.isOnline,
                observationController: _observationController,
              ),
            ],
          ),
        );
    }
  }
}

// ── Board content ──

class _BoardContent extends StatelessWidget {
  final AssignmentBoard board;
  final AssignmentBoardController ctrl;
  final bool isAdmin;
  final bool isOnline;
  final TextEditingController observationController;

  const _BoardContent({
    required this.board,
    required this.ctrl,
    required this.isAdmin,
    required this.isOnline,
    required this.observationController,
  });

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final availableEquines = board.availableEquines
        .where((e) => e.isAvailable)
        .toList();
    final unavailableEquines = board.availableEquines
        .where((e) => !e.isAvailable)
        .toList();
    final availableSaddles = board.availableSaddles
        .where((s) => s.isAvailable)
        .toList();
    final unavailableSaddles = board.availableSaddles
        .where((s) => !s.isAvailable)
        .toList();

    final hasConfirmedAssignments = board.participants.any(
      (p) => p.assignment?.status == AssignmentStatus.confirmed,
    ) || ctrl.hasPendingChanges;
    final hasFinalizedAssignments = board.participants.any(
      (p) => p.assignment?.status == AssignmentStatus.final_,
    );
    final children = <Widget>[
      // ── Summary stats bar ──
      _SummaryBar(summary: board.summary),

      const SizedBox(height: 24),

      if (board.participants.isEmpty)
        _EmptyState(message: 'No hay participantes registrados')
      else
        ...board.participants.map(
          (p) => Padding(
            padding: EdgeInsets.only(bottom: tokens.spaceMd),
            child: _ParticipantAssignmentListItem(
              participant: p,
              availableEquines: board.availableEquines,
              availableSaddles: board.availableSaddles,
              isAdmin: isAdmin,
              isOnline: isOnline,
              ctrl: ctrl,
            ),
          ),
        ),

      // ── Observation text field (both roles when online) ──
      if (isOnline) ...[
        const SizedBox(height: 16),
        TextField(
          controller: observationController,
          decoration: const InputDecoration(
            hintText: 'Agregar observación...',
            border: OutlineInputBorder(),
          ),
          maxLines: 3,
        ),
        const SizedBox(height: 12),
      ],

      // ── General action buttons (admin, online) ──
      if (isAdmin && isOnline) ...[
        if (hasConfirmedAssignments)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: AppButton(
              label: 'Finalizar asignaciones',
              icon: ctrl.isFinalizing ? null : Icons.check_circle_outline_rounded,
              variant: AppButtonVariant.primary,
              expanded: true,
              onPressed: ctrl.isFinalizing
                  ? null
                  : () => _showFinalizeAllConfirm(
                        context,
                        ctrl,
                        observationController,
                      ),
            ),
          ),
        if (hasFinalizedAssignments)
          AppButton(
            label: 'Revertir finalizaciones',
            icon: ctrl.isRevertingFinalize ? null : Icons.undo_rounded,
            variant: AppButtonVariant.ghost,
            expanded: true,
            onPressed: ctrl.isRevertingFinalize
                ? null
                : () => _showUnfinalizeAllConfirm(
                      context,
                      ctrl,
                      observationController,
                    ),
          ),
        const SizedBox(height: 12),
      ],

      const SizedBox(height: 24),

      // ── Available equines section ──
      AppSectionHeader(
        title: 'Equinos disponibles',
        subtitle: '${availableEquines.length} disponibles',
        variant: AppSectionHeaderVariant.compact,
      ),
      const SizedBox(height: 12),
      _AvailableEquinesGrid(equines: availableEquines),

      const SizedBox(height: 24),

      // ── Available saddles section ──
      AppSectionHeader(
        title: 'Sillas disponibles',
        subtitle: '${availableSaddles.length} disponibles',
        variant: AppSectionHeaderVariant.compact,
      ),
      const SizedBox(height: 12),
      _AvailableSaddlesGrid(saddles: availableSaddles),

      if (unavailableEquines.isNotEmpty) ...[
        const SizedBox(height: 24),
        AppSectionHeader(
          title: 'Equinos no disponibles',
          subtitle: '${unavailableEquines.length} bloqueados',
          variant: AppSectionHeaderVariant.compact,
        ),
        const SizedBox(height: 12),
        _AvailableEquinesGrid(equines: unavailableEquines),
      ],

      if (unavailableSaddles.isNotEmpty) ...[
        const SizedBox(height: 24),
        AppSectionHeader(
          title: 'Sillas no disponibles',
          subtitle: '${unavailableSaddles.length} bloqueadas',
          variant: AppSectionHeaderVariant.compact,
        ),
        const SizedBox(height: 12),
        _AvailableSaddlesGrid(saddles: unavailableSaddles),
      ],
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
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

// ── Participant assignment list item ──

void _showFinalizeAllConfirm(
  BuildContext context,
  AssignmentBoardController ctrl,
  TextEditingController obsCtrl,
) {
  AppConfirmDialog.show(
    context: context,
    icon: Icons.check_circle_outline_rounded,
    title: 'Finalizar asignaciones',
    message: '¿Finalizar todas las asignaciones confirmadas?',
    confirmLabel: 'Sí',
    onConfirm: () {
      final notes = obsCtrl.text.trim();
      ctrl.finalizeAll(notes: notes.isEmpty ? null : notes);
      if (notes.isNotEmpty) obsCtrl.clear();
    },
  );
}

void _showUnfinalizeAllConfirm(
  BuildContext context,
  AssignmentBoardController ctrl,
  TextEditingController obsCtrl,
) {
  AppConfirmDialog.show(
    context: context,
    icon: Icons.undo_rounded,
    title: 'Revertir finalizaciones',
    message: 'Todas las asignaciones finalizadas volverán a estado confirmada.',
    confirmLabel: 'Sí',
    style: DialogStyle.warning,
    onConfirm: () {
      final notes = obsCtrl.text.trim();
      ctrl.unfinalizeAll(notes: notes.isEmpty ? null : notes);
      if (notes.isNotEmpty) obsCtrl.clear();
    },
  );
}

class _ParticipantAssignmentListItem extends StatelessWidget {
  final BoardParticipant participant;
  final List<AvailableEquine> availableEquines;
  final List<AvailableSaddle> availableSaddles;
  final bool isAdmin;
  final bool isOnline;
  final AssignmentBoardController ctrl;

  const _ParticipantAssignmentListItem({
    required this.participant,
    required this.availableEquines,
    required this.availableSaddles,
    required this.isAdmin,
    required this.isOnline,
    required this.ctrl,
  });

  @override
  Widget build(BuildContext context) {
    final assignment = participant.assignment;
    final hasBlockingIssues = participant.blockingReasons.isNotEmpty;
    final isBusy = ctrl.isCreating ||
        ctrl.isUpdating ||
        ctrl.isFinalizing ||
        ctrl.isRemoving ||
        ctrl.isRevertingFinalize;

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
      } else if (assignment.status == AssignmentStatus.final_ ||
          assignment.status == AssignmentStatus.draft) {
        cardState = AppAssignmentCardState.ok;
        validationMessage = null;
      } else if (assignment.status == AssignmentStatus.confirmed) {
        cardState = AppAssignmentCardState.ok;
        validationMessage = null;
      } else {
        cardState = AppAssignmentCardState.warning;
        validationMessage =
            'Estado: ${assignment.status?.name ?? "desconocido"}';
      }
    }

    final equineMaxWeight = () {
      if (assignment?.equineId == null) return null;
      final eq = availableEquines.cast<AvailableEquine?>().firstWhere(
        (e) => e?.id == assignment!.equineId,
        orElse: () => null,
      );
      return eq?.maxRiderWeightKg;
    }();

    return Column(
      children: [
        AppAssignmentListItem(
          participant: AppAssignmentParticipantData(
            name: participant.fullName,
            weightLabel:
                '${participant.weightKg?.toStringAsFixed(0) ?? "?"} kg',
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
            image: _equineImageProvider(assignment?.equineId),
          ),
          saddleLabel: assignment?.saddleLabel ?? '—',
          isFinalized: assignment?.status == AssignmentStatus.final_,
          onChangeEquine:
              isAdmin &&
                  isOnline &&
                  !isBusy &&
                  assignment?.status != AssignmentStatus.final_
              ? () => _showEquinePicker(context, participant)
              : null,
          onChangeSaddle:
              isAdmin &&
                  isOnline &&
                  !isBusy &&
                  assignment != null &&
                  assignment.status != AssignmentStatus.final_
              ? () => _showSaddlePicker(context, participant)
              : null,
          onRemoveAssignment:
              isAdmin &&
                  isOnline &&
                  !isBusy &&
                  assignment != null &&
                  assignment.status != AssignmentStatus.final_
              ? () => _showRemoveConfirm(context)
              : null,
          onRemoveSaddle:
              isAdmin &&
                  isOnline &&
                  !isBusy &&
                  assignment != null &&
                  assignment.status != AssignmentStatus.final_ &&
                  assignment.saddleId != null
              ? () => _showRemoveSaddleConfirm(context)
              : null,
          onRevertFinalize: null,
          state: cardState,
          validationMessage: validationMessage,
          safetyFlags: assignment?.warnings ?? [],
        ),

        // ── Action error for this participant ──
        if (ctrl.actionError != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              ctrl.actionError!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.error,
              ),
            ),
          ),
      ],
    );
  }

  void _showEquinePicker(BuildContext context, BoardParticipant participant) {
    final currentEquineId = participant.assignment?.equineId;
    final isCreating = participant.assignment == null;
    final equines = availableEquines.where((e) => e.isAvailable).toList();
    String? selectedEquineId = currentEquineId;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) {
          return AlertDialog(
            title: Text(
              isCreating
                  ? 'Asignar equino a ${participant.fullName}'
                  : 'Cambiar equino de ${participant.fullName}',
            ),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (equines.isEmpty)
                    const Text('No hay equinos disponibles')
                  else
                    ...equines.map(
                      (eq) => RadioListTile<String>(
                        title: Text(eq.name),
                        subtitle: eq.maxRiderWeightKg != null
                            ? Text('Máx ${eq.maxRiderWeightKg} kg')
                            : null,
                        value: eq.id,
                        groupValue: selectedEquineId,
                        onChanged: (v) =>
                            setDialogState(() => selectedEquineId = v),
                      ),
                    ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Cancelar'),
              ),
              ElevatedButton(
                onPressed:
                    selectedEquineId == null ||
                        ctrl.isCreating ||
                        ctrl.isUpdating
                    ? null
                    : () {
                        Navigator.of(ctx).pop();
                        if (isCreating) {
                          ctrl.create(
                            participantId: participant.participantId,
                            equineId: selectedEquineId!,
                          );
                        } else {
                          ctrl.update(
                            assignmentId: participant.assignment!.assignmentId!,
                            equineId: selectedEquineId!,
                          );
                        }
                      },
                child: (ctrl.isCreating || ctrl.isUpdating)
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(isCreating ? 'Asignar' : 'Cambiar'),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showSaddlePicker(BuildContext context, BoardParticipant participant) {
    final aid = participant.assignment?.assignmentId;
    if (aid == null) return;
    final currentSaddleId = participant.assignment?.saddleId;
    final saddles = availableSaddles.where((s) => s.isAvailable).toList();
    String? selectedSaddleId = currentSaddleId;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) {
          return AlertDialog(
            title: Text('Asignar silla a ${participant.fullName}'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (saddles.isEmpty)
                    const Text('No hay sillas disponibles')
                  else
                    ...saddles.map(
                      (saddle) => RadioListTile<String>(
                        title: Text(saddle.name ?? saddle.code),
                        value: saddle.id,
                        groupValue: selectedSaddleId,
                        onChanged: (v) =>
                            setDialogState(() => selectedSaddleId = v),
                      ),
                    ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Cancelar'),
              ),
              ElevatedButton(
                onPressed: selectedSaddleId == null || ctrl.isUpdating
                    ? null
                    : () {
                        Navigator.of(ctx).pop();
                        ctrl.update(
                          assignmentId: aid,
                          saddleId: selectedSaddleId!,
                        );
                      },
                child: ctrl.isUpdating
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Asignar'),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showRemoveSaddleConfirm(BuildContext context) {
    final aid = participant.assignment?.assignmentId;
    if (aid == null) return;

    AppConfirmDialog.show(
      context: context,
      icon: Icons.delete_outline_rounded,
      title: 'Quitar silla',
      message: '¿Quitar la silla asignada a ${participant.fullName}?',
      confirmLabel: 'Sí',
      style: DialogStyle.danger,
      onConfirm: () => ctrl.update(assignmentId: aid, saddleId: null),
    );
  }

  void _showRemoveConfirm(BuildContext context) {
    final aid = participant.assignment?.assignmentId;
    final title = 'Quitar asignación';
    final message = '¿Quitar la asignación de ${participant.fullName}?';

    if (aid != null) {
      AppConfirmDialog.show(
        context: context,
        icon: Icons.delete_outline_rounded,
        title: title,
        message: message,
        confirmLabel: 'Sí',
        style: DialogStyle.danger,
        onConfirm: () => ctrl.remove(aid),
      );
    } else {
      AppConfirmDialog.show(
        context: context,
        icon: Icons.delete_outline_rounded,
        title: title,
        message: message,
        confirmLabel: 'Sí',
        style: DialogStyle.danger,
        onConfirm: () => ctrl.removePending(participant.participantId),
      );
    }
  }

  ImageProvider? _equineImageProvider(String? equineId) {
    if (equineId == null) return null;
    final eq = availableEquines.cast<AvailableEquine?>().firstWhere(
      (item) => item?.id == equineId,
      orElse: () => null,
    );
    final encoded = eq?.imageBase64?.trim();
    if (encoded == null || encoded.isEmpty) return null;
    try {
      final bytes = base64Decode(encoded);
      if (!_looksLikeImage(bytes)) return null;
      return MemoryImage(bytes);
    } catch (_) {
      return null;
    }
  }

  bool _looksLikeImage(List<int> bytes) {
    if (bytes.length < 4) return false;
    // PNG
    if (bytes[0] == 0x89 &&
        bytes[1] == 0x50 &&
        bytes[2] == 0x4E &&
        bytes[3] == 0x47) {
      return true;
    }
    // JPEG
    if (bytes[0] == 0xFF && bytes[1] == 0xD8) return true;
    // GIF
    if (bytes[0] == 0x47 && bytes[1] == 0x49 && bytes[2] == 0x46) return true;
    // WEBP
    if (bytes.length >= 12 &&
        bytes[0] == 0x52 &&
        bytes[1] == 0x49 &&
        bytes[2] == 0x46 &&
        bytes[3] == 0x46 &&
        bytes[8] == 0x57 &&
        bytes[9] == 0x45 &&
        bytes[10] == 0x42 &&
        bytes[11] == 0x50) {
      return true;
    }
    return false;
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
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
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
            Icon(Icons.error_outline_rounded, size: 48, color: scheme.error),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(
                context,
              ).textTheme.bodyLarge?.copyWith(color: scheme.onSurfaceVariant),
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
