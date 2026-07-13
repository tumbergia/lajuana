import 'package:flutter/material.dart';

import 'package:mobile_ui/src/theme/app_colors.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_domain/src/reservations/reservation_payment_proof_detail.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservation_detail_controller.dart';

/// Shows a dialog with a form to reject a payment proof with a reason.
Future<void> showRejectDialog(
  BuildContext context,
  ReservationPaymentProofDetail proof,
  ReservationDetailController controller,
  bool isAdmin,
) async {
  final reasonCtrl = TextEditingController();
  final formKey = GlobalKey<FormState>();

  showDialog(
    context: context,
    builder: (ctx) {
      final scheme = Theme.of(ctx).colorScheme;
      final tokens = Theme.of(ctx).appTokens;

      return AlertDialog(
        backgroundColor: scheme.surfaceContainerHigh,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: tokens.radiusXl,
        ),
        insetPadding:
            const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
        contentPadding: EdgeInsets.zero,
        content: Form(
          key: formKey,
          child: Padding(
            padding: EdgeInsets.all(tokens.spaceXl),
              child: SizedBox(
              height: 320,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Icon(Icons.cancel_rounded,
                      size: 48, color: AppColors.danger),
                  SizedBox(height: tokens.spaceLg),
                  Text(
                    'Rechazar comprobante',
                    textAlign: TextAlign.center,
                    style: Theme.of(ctx)
                        .textTheme
                        .titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  SizedBox(height: tokens.spaceSm),
                  Text(
                    'Indica el motivo del rechazo',
                    textAlign: TextAlign.center,
                    style: Theme.of(ctx)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(color: scheme.onSurfaceVariant),
                  ),
                  SizedBox(height: tokens.spaceLg),
                  AppTextField(
                    controller: reasonCtrl,
                    hintText: 'Motivo del rechazo',
                    maxLines: 3,
                    variant: AppTextFieldVariant.filled,
                  ),
                  SizedBox(height: tokens.spaceXl),
                  Row(
                    children: [
                      Expanded(
                        child: AppButton(
                          label: 'Cancelar',
                          variant: AppButtonVariant.secondary,
                          onPressed: () => Navigator.of(ctx).pop(),
                          expanded: true,
                          height: 48,
                        ),
                      ),
                      SizedBox(width: tokens.spaceSm),
                      Expanded(
                        child: AppButton(
                          label: 'Rechazar',
                          variant: AppButtonVariant.danger,
                          onPressed: () {
                            final reason = reasonCtrl.text.trim();
                            if (reason.isEmpty) {
                              showAppToast(
                                context,
                                message: 'Debes indicar un motivo',
                                isError: true,
                              );
                              return;
                            }
                            Navigator.of(ctx).pop();
                            controller.rejectPaymentProof(
                              paymentProofId: proof.id,
                              reason: reason,
                              isAdmin: isAdmin,
                            );
                          },
                          expanded: true,
                          height: 48,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    },
  );
}
