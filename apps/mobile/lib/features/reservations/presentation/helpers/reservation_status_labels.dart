import '../../../../app/widgets/app_badge.dart';

/// Labels y tonos para estados de reserva (formulario, pago, proofs).
///
/// Centraliza la lógica para evitar duplicación entre widgets
/// que muestran estos estados.

String formStatusLabel(String status) {
  switch (status.toLowerCase()) {
    case 'not_sent':
      return 'No enviado';
    case 'sent':
      return 'Enviado';
    case 'partial':
      return 'Parcial';
    case 'complete':
      return 'Completo';
    case 'revoked':
      return 'Revocado';
    case 'accepted':
      return 'Aceptado';
    default:
      return status;
  }
}

AppBadgeTone formStatusTone(String status) {
  switch (status.toLowerCase()) {
    case 'complete':
      return AppBadgeTone.success;
    case 'partial':
      return AppBadgeTone.warning;
    case 'revoked':
      return AppBadgeTone.danger;
    default:
      return AppBadgeTone.neutral;
  }
}

String paymentStatusLabel(String? status) {
  switch (status?.toLowerCase()) {
    case 'pending':
      return 'Pendiente';
    case 'received':
      return 'Recibido';
    case 'verified':
      return 'Verificado';
    case 'rejected':
      return 'Rechazado';
    case 'accepted':
      return 'Aceptado';
    default:
      return status ?? 'Sin informacion';
  }
}

String paymentProofStatusLabel(String? status) {
  switch (status?.toLowerCase()) {
    case 'pending':
      return 'Pendiente';
    case 'received':
      return 'Recibido';
    case 'verified':
      return 'Verificado';
    case 'rejected':
      return 'Rechazado';
    default:
      return status ?? 'Sin estado';
  }
}

AppBadgeTone paymentProofStatusTone(String? status) {
  switch (status?.toLowerCase()) {
    case 'pending':
      return AppBadgeTone.warning;
    case 'received':
      return AppBadgeTone.primary;
    case 'verified':
      return AppBadgeTone.success;
    case 'rejected':
      return AppBadgeTone.danger;
    default:
      return AppBadgeTone.neutral;
  }
}
