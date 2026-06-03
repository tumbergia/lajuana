// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentProofUpdateSchema`.

class PaymentProofUpdate {

  final String? reservationId;
  final String? filename;
  final String? contentType;
  final String? sizeBytes;
  final String? sha256;

  const PaymentProofUpdate(
    {
    this.reservationId,
    this.filename,
    this.contentType,
    this.sizeBytes,
    this.sha256,
    }
  );

  factory PaymentProofUpdate.fromJson(Map<String, dynamic> json) {
    return PaymentProofUpdate(
      reservationId: json['reservation_id'] as String?,
      filename: json['filename'] as String?,
      contentType: json['content_type'] as String?,
      sizeBytes: json['size_bytes'] as String?,
      sha256: json['sha256'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'reservation_id': reservationId,
    'filename': filename,
    'content_type': contentType,
    'size_bytes': sizeBytes,
    'sha256': sha256,
  };

}
