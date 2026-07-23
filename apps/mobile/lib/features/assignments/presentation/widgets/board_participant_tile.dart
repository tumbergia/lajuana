import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_confirm_dialog.dart';
import 'package:mobile_ui/src/widgets/cards/app_assignment_card.dart';
import 'package:mobile_ui/src/widgets/cards/app_assignment_list_item.dart';
import 'package:mobile_domain/src/assignments/assignment_board.dart';
import 'package:mobile_domain/mobile_domain.dart';
import 'package:mobile/features/assignments/presentation/controllers/assignment_board_controller.dart';
import 'package:mobile/features/assignments/presentation/helpers/assignment_status_labels.dart';

/// Widget que muestra la asignación de un participante con botones de acción
/// y dialegs emergentes para elegir equino/silla.
class BoardParticipantTile extends StatelessWidget {
  final BoardParticipant participant;
  final List<AvailableEquine> availableEquines;
  final List<AvailableSaddle> availableSaddles;
  final bool isAdmin;
  final bool isOnline;
  final AssignmentBoardController ctrl;

  const BoardParticipantTile({
    super.key,
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

    final AppAssignmentCardState cardState;
    final String? validationMessage;

    if (assignment == null) {
      if (hasBlockingIssues) {
        cardState = AppAssignmentCardState.error;
        validationMessage = participant.blockingReasons.join('\n');
      } else {
        cardState = AppAssignmentCardState.warning;
        validationMessage = 'Pendiente de asignación';
      }
    } else {
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
            'Estado: ${assignmentStatusLabel(assignment.status)}';
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
            statusLabel: assignmentStatusLabel(assignment?.status),
            image: _equineImageProvider(assignment?.equineId),
          ),
          saddleLabel: assignment?.saddleLabel ?? '—',
          isFinalized: assignment?.status == AssignmentStatus.final_,
          onChangeEquine:
              isAdmin && isOnline && !isBusy && assignment?.status != AssignmentStatus.final_
                  ? () => _showEquinePicker(context)
                  : null,
          onChangeSaddle:
              isAdmin && isOnline && !isBusy && assignment != null && assignment.status != AssignmentStatus.final_
                  ? () => _showSaddlePicker(context)
                  : null,
          onRemoveAssignment:
              isAdmin && isOnline && !isBusy && assignment != null && assignment.status != AssignmentStatus.final_
                  ? () => _showRemoveConfirm(context)
                  : null,
          onRemoveSaddle:
              isAdmin && isOnline && !isBusy && assignment != null && assignment.status != AssignmentStatus.final_ && assignment.saddleId != null
                  ? () => _showRemoveSaddleConfirm(context)
                  : null,
          onRevertFinalize: isAdmin &&
                  isOnline &&
                  !isBusy &&
                  assignment?.status == AssignmentStatus.final_ &&
                  assignment?.assignmentId != null
              ? () => ctrl.unfinalizeAssignment(assignment!.assignmentId!)
              : null,
          state: cardState,
          validationMessage: validationMessage,
          safetyFlags: assignment?.warnings ?? [],
        ),
      ],
    );
  }

  // ── Equine picker dialog ──

  void _showEquinePicker(BuildContext context) {
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
                    selectedEquineId == null || ctrl.isCreating || ctrl.isUpdating
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

  // ── Saddle picker dialog ──

  void _showSaddlePicker(BuildContext context) {
    final participantId = participant.participantId;
    final aid = participant.assignment?.assignmentId;
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
                        if (aid != null) {
                          ctrl.update(
                            assignmentId: aid,
                            saddleId: selectedSaddleId!,
                          );
                        } else {
                          ctrl.assignSaddle(
                            participantId: participantId,
                            saddleId: selectedSaddleId!,
                          );
                        }
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

  // ── Remove confirmations ──

  void _showRemoveSaddleConfirm(BuildContext context) {
    final participantId = participant.participantId;
    final aid = participant.assignment?.assignmentId;

    AppConfirmDialog.show(
      context: context,
      icon: Icons.delete_outline_rounded,
      title: 'Quitar silla',
      message: '¿Quitar la silla asignada a ${participant.fullName}?',
      confirmLabel: 'Sí',
      style: DialogStyle.danger,
      onConfirm: () {
        if (aid != null) {
          ctrl.update(assignmentId: aid, saddleId: null);
        } else {
          ctrl.assignSaddle(participantId: participantId, saddleId: null);
        }
      },
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

  // ── Image helpers ──

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
    if (bytes[0] == 0x89 && bytes[1] == 0x50 && bytes[2] == 0x4E && bytes[3] == 0x47) return true;
    if (bytes[0] == 0xFF && bytes[1] == 0xD8) return true;
    if (bytes[0] == 0x47 && bytes[1] == 0x49 && bytes[2] == 0x46) return true;
    if (bytes.length >= 12 && bytes[0] == 0x52 && bytes[1] == 0x49 && bytes[2] == 0x46 && bytes[3] == 0x46 && bytes[8] == 0x57 && bytes[9] == 0x45 && bytes[10] == 0x42 && bytes[11] == 0x50) return true;
    return false;
  }

  String? _experienceLabel(String? level) {
    if (level == null) return null;
    switch (level) {
      case 'basic': return 'Básico';
      case 'intermediate': return 'Intermedio';
      case 'advanced': return 'Avanzado';
      default: return level;
    }
  }
}
