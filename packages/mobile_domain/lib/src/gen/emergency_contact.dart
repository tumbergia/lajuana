// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EmergencyContactSchema`.

class EmergencyContact {

  final String name;
  final String phone;
  final String? relationship;
  final String? country;

  const EmergencyContact(
    {
    required this.name,
    required this.phone,
    this.relationship,
    this.country,
    }
  );

  factory EmergencyContact.fromJson(Map<String, dynamic> json) {
    return EmergencyContact(
      name: json['name'] as String,
      phone: json['phone'] as String,
      relationship: json['relationship'] as String?,
      country: json['country'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'phone': phone,
    'relationship': relationship,
    'country': country,
  };

}
