// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ProviderResponseSchema`.

import 'provider_status.dart';
import 'provider_type.dart';

class Provider {
  final int version;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? deletedAt;
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
  final String capacityNotes;
  final String operationalNotes;
  final String tariffNotes;
  final String sourceNotes;
  final bool isActive;

  const Provider({
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
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
    required this.capacityNotes,
    required this.operationalNotes,
    required this.tariffNotes,
    required this.sourceNotes,
    required this.isActive,
  });

  factory Provider.fromJson(Map<String, dynamic> json) {
    return Provider(
      version: json['version'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      deletedAt: json['deleted_at'] as String?,
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
      capacityNotes: json['capacity_notes'] as String,
      operationalNotes: json['operational_notes'] as String,
      tariffNotes: json['tariff_notes'] as String,
      sourceNotes: json['source_notes'] as String,
      isActive: json['is_active'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
    'version': version,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
    'deleted_at': deletedAt,
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
    'capacity_notes': capacityNotes,
    'operational_notes': operationalNotes,
    'tariff_notes': tariffNotes,
    'source_notes': sourceNotes,
    'is_active': isActive,
  };
}
