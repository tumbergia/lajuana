// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `FileInitUploadRequestSchema`.

class FileInitUpload {

  final String context;
  final String filename;
  final String mimeType;
  final int sizeBytes;
  final String sha256Hash;

  const FileInitUpload(
    {
    required this.context,
    required this.filename,
    required this.mimeType,
    required this.sizeBytes,
    required this.sha256Hash,
    }
  );

  factory FileInitUpload.fromJson(Map<String, dynamic> json) {
    return FileInitUpload(
      context: json['context'] as String,
      filename: json['filename'] as String,
      mimeType: json['mime_type'] as String,
      sizeBytes: json['size_bytes'] as int,
      sha256Hash: json['sha256_hash'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'context': context,
    'filename': filename,
    'mime_type': mimeType,
    'size_bytes': sizeBytes,
    'sha256_hash': sha256Hash,
  };

}
