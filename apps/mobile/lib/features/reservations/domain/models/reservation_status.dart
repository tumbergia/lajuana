enum ReservationStatus {
  contact,
  quoted,
  preReserved,
  pendingPayment,
  paymentReceived,
  confirmed,
  cancelled,
  completed,
  expired,
  unknown,
}

ReservationStatus parseReservationStatus(String? value) {
  if (value == null) return ReservationStatus.unknown;
  switch (value.toLowerCase()) {
    case 'contact':
      return ReservationStatus.contact;
    case 'quoted':
      return ReservationStatus.quoted;
    case 'pre_reserved':
    case 'prereserved':
      return ReservationStatus.preReserved;
    case 'pending_payment':
    case 'pendingpayment':
      return ReservationStatus.pendingPayment;
    case 'payment_received':
    case 'paymentreceived':
      return ReservationStatus.paymentReceived;
    case 'confirmed':
      return ReservationStatus.confirmed;
    case 'cancelled':
      return ReservationStatus.cancelled;
    case 'completed':
      return ReservationStatus.completed;
    case 'expired':
      return ReservationStatus.expired;
    default:
      return ReservationStatus.unknown;
  }
}

String reservationStatusLabel(ReservationStatus status) {
  switch (status) {
    case ReservationStatus.contact:
      return 'Contacto';
    case ReservationStatus.quoted:
      return 'Cotizada';
    case ReservationStatus.preReserved:
      return 'Pre-reservada';
    case ReservationStatus.pendingPayment:
      return 'Pendiente de pago';
    case ReservationStatus.paymentReceived:
      return 'Comprobante recibido';
    case ReservationStatus.confirmed:
      return 'Confirmada';
    case ReservationStatus.cancelled:
      return 'Cancelada';
    case ReservationStatus.completed:
      return 'Completada';
    case ReservationStatus.expired:
      return 'Expirada';
    case ReservationStatus.unknown:
      return 'Desconocido';
  }
}
