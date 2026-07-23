// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ProviderListItemSchema`.

import 'provider_status.dart';
import 'provider_type.dart';

class ProviderListItem {
  final String id;
  final String name;
  final String slug;
  final ProviderType type;
  final ProviderStatus status;
  final List<String> serviceCategories;
  final String contactName;
  final String email;
  final String whatsappPhone;
  final String locationLabel;
  final bool isActive;

  const ProviderListItem({
    required this.id,
    required this.name,
    required this.slug,
    required this.type,
    required this.status,
    required this.serviceCategories,
    required this.contactName,
    required this.email,
    required this.whatsappPhone,
    required this.locationLabel,
    required this.isActive,
  });

  factory ProviderListItem.fromJson(Map<String, dynamic> json) {
    return ProviderListItem(
      id: json['id'] as String,
      name: json['name'] as String,
      slug: json['slug'] as String,
      type: (json['type'] as String).toProviderType(),
      status: (json['status'] as String).toProviderStatus(),
      serviceCategories: (json['service_categories'] as List<dynamic>)
          .cast<String>(),
      contactName: json['contact_name'] as String,
      email: json['email'] as String,
      whatsappPhone: json['whatsapp_phone'] as String,
      locationLabel: json['location_label'] as String,
      isActive: json['is_active'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'slug': slug,
    'type': type.toJson(),
    'status': status.toJson(),
    'service_categories': serviceCategories,
    'contact_name': contactName,
    'email': email,
    'whatsapp_phone': whatsappPhone,
    'location_label': locationLabel,
    'is_active': isActive,
  };
}
