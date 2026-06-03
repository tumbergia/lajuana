// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `EmergencyContactsResponseSchema`.

import 'emergency_catalog_contact.dart';

class EmergencyContacts {

  final List<EmergencyCatalogContact> items;

  const EmergencyContacts(
    {
    required this.items,
    }
  );

  factory EmergencyContacts.fromJson(Map<String, dynamic> json) {
    return EmergencyContacts(
      items: (json['items'] as List<dynamic>?)
        ?.map((e) => EmergencyCatalogContact.fromJson(e as Map<String, dynamic>)).toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() => {
    'items': items,
  };

}
