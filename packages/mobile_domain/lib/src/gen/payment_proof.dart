// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PaymentProofResponseSchema`.

import 'payment_status.dart';

class PaymentProof {

  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String reservationId;
  final String storageKey;
  final String filename;
  final String contentType;
  final int sizeBytes;
  final String sha256;
  final PaymentStatus status;
  final DateTime uploadedAt;

  const PaymentProof(
    {
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.reservationId,
    required this.storageKey,
    required this.filename,
    required this.contentType,
    required this.sizeBytes,
    required this.sha256,
    required this.status,
    required this.uploadedAt,
    }
  );

  factory PaymentProof.fromJson(Map<String, dynamic> json) {
    return PaymentProof(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      reservationId: json['reservation_id'] as String,
      storageKey: json['storage_key'] as String,
      filename: json['filename'] as String,
      contentType: json['content_type'] as String,
      sizeBytes: json['size_bytes'] as int,
      sha256: json['sha256'] as String,
      status: (json['status'] as String).toPaymentStatus(),
      uploadedAt: DateTime.parse(json['uploaded_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'reservation_id': reservationId,
    'storage_key': storageKey,
    'filename': filename,
    'content_type': contentType,
    'size_bytes': sizeBytes,
    'sha256': sha256,
    'status': status.toJson(),
    'uploaded_at': uploadedAt.toIso8601String(),
  };

}
