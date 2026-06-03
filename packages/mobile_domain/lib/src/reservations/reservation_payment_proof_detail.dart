import '../gen/payment_proof.dart' as gen;

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

  /// Crea un [ReservationPaymentProofDetail] de dominio desde el modelo generado.
  factory ReservationPaymentProofDetail.fromGen(gen.PaymentProof source) {
    return ReservationPaymentProofDetail(
      id: source.id,
      reservationId: source.reservationId,
      filename: source.filename,
      contentType: source.contentType,
      sizeBytes: source.sizeBytes,
      status: source.status.value,
      uploadedAt: source.uploadedAt,
      storageKey: source.storageKey,
      sha256: source.sha256,
    );
  }

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
