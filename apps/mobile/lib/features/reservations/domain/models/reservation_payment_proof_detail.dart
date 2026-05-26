/// Payment proof detail within a reservation.
/// Carries enough info for the read-only payment section.
class ReservationPaymentProofDetail {
  const ReservationPaymentProofDetail({
    required this.id,
    required this.reservationId,
    this.filename,
    this.contentType,
    this.sizeBytes,
    this.status,
    this.uploadedAt,
    this.storageKey,
    this.sha256,
  });

  final String id;
  final String reservationId;
  final String? filename;
  final String? contentType;
  final int? sizeBytes;
  final String? status;
  final DateTime? uploadedAt;
  final String? storageKey;
  final String? sha256;
}
