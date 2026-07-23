// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ServiceLogPhotoUploadResponseSchema`.

class ServiceLogPhotoUpload {
  final String storageKey;
  final String filename;
  final String contentType;
  final int sizeBytes;

  const ServiceLogPhotoUpload({
    required this.storageKey,
    required this.filename,
    required this.contentType,
    required this.sizeBytes,
  });

  factory ServiceLogPhotoUpload.fromJson(Map<String, dynamic> json) {
    return ServiceLogPhotoUpload(
      storageKey: json['storage_key'] as String,
      filename: json['filename'] as String,
      contentType: json['content_type'] as String,
      sizeBytes: json['size_bytes'] as int,
    );
  }

  Map<String, dynamic> toJson() => {
    'storage_key': storageKey,
    'filename': filename,
    'content_type': contentType,
    'size_bytes': sizeBytes,
  };
}
