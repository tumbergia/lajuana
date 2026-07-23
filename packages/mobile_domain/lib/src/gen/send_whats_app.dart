// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `SendWhatsAppRequest`.

class SendWhatsApp {

  final String toPhone;
  final String message;

  const SendWhatsApp(
    {
    required this.toPhone,
    required this.message,
    }
  );

  factory SendWhatsApp.fromJson(Map<String, dynamic> json) {
    return SendWhatsApp(
      toPhone: json['to_phone'] as String,
      message: json['message'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'to_phone': toPhone,
    'message': message,
  };

}
