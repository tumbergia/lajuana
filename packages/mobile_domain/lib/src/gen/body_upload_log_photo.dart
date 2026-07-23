// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `Body_uploadLogPhoto`.

class Body_uploadLogPhoto {

  final String file;

  const Body_uploadLogPhoto(
    {
    required this.file,
    }
  );

  factory Body_uploadLogPhoto.fromJson(Map<String, dynamic> json) {
    return Body_uploadLogPhoto(
      file: json['file'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'file': file,
  };

}
