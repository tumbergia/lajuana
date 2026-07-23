// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `PolicyUpdateSchema`.

class PolicyUpdate {
  final String? providerId;
  final String? policyNumber;
  final String? issuedAt;
  final String? expiresAt;
  final String? notes;

  const PolicyUpdate({
    this.providerId,
    this.policyNumber,
    this.issuedAt,
    this.expiresAt,
    this.notes,
  });

  factory PolicyUpdate.fromJson(Map<String, dynamic> json) {
    return PolicyUpdate(
      providerId: json['provider_id'] as String?,
      policyNumber: json['policy_number'] as String?,
      issuedAt: json['issued_at'] as String?,
      expiresAt: json['expires_at'] as String?,
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'provider_id': providerId,
    'policy_number': policyNumber,
    'issued_at': issuedAt,
    'expires_at': expiresAt,
    'notes': notes,
  };
}
