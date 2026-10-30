// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EmergencyCatalogContactSchema`.

class EmergencyCatalogContact {
  final String code;
  final String name;
  final String description;
  final String phoneNumber;
  final String category;
  final bool isPrimary;
  final bool isNational;

  const EmergencyCatalogContact({
    required this.code,
    required this.name,
    required this.description,
    required this.phoneNumber,
    required this.category,
    required this.isPrimary,
    required this.isNational,
  });

  factory EmergencyCatalogContact.fromJson(Map<String, dynamic> json) {
    return EmergencyCatalogContact(
      code: json['code'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      phoneNumber: json['phone_number'] as String,
      category: json['category'] as String,
      isPrimary: json['is_primary'] as bool,
      isNational: json['is_national'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'code': code,
    'name': name,
    'description': description,
    'phone_number': phoneNumber,
    'category': category,
    'is_primary': isPrimary,
    'is_national': isNational,
  };
}
