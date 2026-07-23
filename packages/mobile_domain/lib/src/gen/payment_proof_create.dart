// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentProofCreateSchema`.

class PaymentProofCreate {

  final String filename;
  final String contentType;
  final int sizeBytes;
  final String sha256;
  final String storageKey;

  const PaymentProofCreate(
    {
    required this.filename,
    required this.contentType,
    required this.sizeBytes,
    required this.sha256,
    required this.storageKey,
    }
  );

  factory PaymentProofCreate.fromJson(Map<String, dynamic> json) {
    return PaymentProofCreate(
      filename: json['filename'] as String,
      contentType: json['content_type'] as String,
      sizeBytes: json['size_bytes'] as int,
      sha256: json['sha256'] as String,
      storageKey: json['storage_key'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'filename': filename,
    'content_type': contentType,
    'size_bytes': sizeBytes,
    'sha256': sha256,
    'storage_key': storageKey,
  };

}
