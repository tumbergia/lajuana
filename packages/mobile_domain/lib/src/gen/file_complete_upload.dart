// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `FileCompleteUploadResponseSchema`.

class FileCompleteUpload {
  final String uploadId;
  final String storageKey;
  final int sizeBytes;
  final String sha256Hash;
  final String status;

  const FileCompleteUpload({
    required this.uploadId,
    required this.storageKey,
    required this.sizeBytes,
    required this.sha256Hash,
    required this.status,
  });

  factory FileCompleteUpload.fromJson(Map<String, dynamic> json) {
    return FileCompleteUpload(
      uploadId: json['upload_id'] as String,
      storageKey: json['storage_key'] as String,
      sizeBytes: json['size_bytes'] as int,
      sha256Hash: json['sha256_hash'] as String,
      status: json['status'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'upload_id': uploadId,
    'storage_key': storageKey,
    'size_bytes': sizeBytes,
    'sha256_hash': sha256Hash,
    'status': status,
  };
}
