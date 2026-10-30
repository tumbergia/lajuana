import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_confirm_dialog.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_proof_detail.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_detail_controller.dart';

/// Shows a confirmation dialog for approving a payment proof.
Future<void> showApproveConfirmationDialog(
  BuildContext context,
  ReservationPaymentProofDetail proof,
  ReservationDetailController controller,
  bool isAdmin,
) async {
  return AppConfirmDialog.show(
    context: context,
    icon: Icons.check_circle_outline_rounded,
    title: 'Aprobar comprobante',
    message:
        'El pago quedará validado, pero la reserva no se '
        'confirmará automáticamente.',
    confirmLabel: 'Aprobar',
    height: 280,
    onConfirm: () {
      controller.approvePaymentProof(
        paymentProofId: proof.id,
        isAdmin: isAdmin,
      );
    },
  );
}
