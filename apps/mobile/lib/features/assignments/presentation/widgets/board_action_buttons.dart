import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_confirm_dialog.dart';
import 'package:mobile/features/assignments/presentation/controllers/assignment_board_controller.dart';

/// Muestra diálogo de confirmación para finalizar todas las asignaciones.
void showFinalizeAllConfirm(
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

/// Muestra diálogo de confirmación para revertir finalizaciones.
void showUnfinalizeAllConfirm(
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
