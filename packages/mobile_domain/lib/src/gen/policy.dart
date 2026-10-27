// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PolicyResponseSchema`.

class Policy {
  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
  final String id;
  final String reservationId;
  final String providerId;
  final String policyNumber;
  final String issuedAt;
  final String expiresAt;
  final String notes;

  const Policy({
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.id,
    required this.reservationId,
    required this.providerId,
    required this.policyNumber,
    required this.issuedAt,
    required this.expiresAt,
    required this.notes,
  });

  factory Policy.fromJson(Map<String, dynamic> json) {
    return Policy(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
      id: json['id'] as String,
      reservationId: json['reservation_id'] as String,
      providerId: json['provider_id'] as String,
      policyNumber: json['policy_number'] as String,
      issuedAt: json['issued_at'] as String,
      expiresAt: json['expires_at'] as String,
      notes: json['notes'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
    'id': id,
    'reservation_id': reservationId,
    'provider_id': providerId,
    'policy_number': policyNumber,
    'issued_at': issuedAt,
    'expires_at': expiresAt,
    'notes': notes,
  };
}
