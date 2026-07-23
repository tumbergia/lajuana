// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ServiceLogPhotoSchema`.

class ServiceLogPhoto {

  final int index;
  final String storageKey;
  final String filename;
  final String contentType;
  final int? sizeBytes;

  const ServiceLogPhoto(
    {
    required this.index,
    required this.storageKey,
    required this.filename,
    required this.contentType,
    this.sizeBytes,
    }
  );

  factory ServiceLogPhoto.fromJson(Map<String, dynamic> json) {
    return ServiceLogPhoto(
      index: json['index'] as int,
      storageKey: json['storage_key'] as String,
      filename: json['filename'] as String,
      contentType: json['content_type'] as String,
      sizeBytes: json['size_bytes'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
    'index': index,
    'storage_key': storageKey,
    'filename': filename,
    'content_type': contentType,
    'size_bytes': sizeBytes,
  };

}
