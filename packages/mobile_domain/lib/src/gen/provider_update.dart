// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

/// AUTO-GENERATED from OpenAPI schema `ProviderUpdateSchema`.

class ProviderUpdate {

  final String? name;
  final String? slug;
  final String? type;
  final String? status;
  final String? serviceCategories;
  final String? contactName;
  final String? email;
  final String? whatsappPhone;
  final String? locationLabel;
  final String? capacityNotes;
  final String? operationalNotes;
  final String? tariffNotes;
  final String? sourceNotes;
  final String? isActive;

  const ProviderUpdate(
    {
    this.name,
    this.slug,
    this.type,
    this.status,
    this.serviceCategories,
    this.contactName,
    this.email,
    this.whatsappPhone,
    this.locationLabel,
    this.capacityNotes,
    this.operationalNotes,
    this.tariffNotes,
    this.sourceNotes,
    this.isActive,
    }
  );

  factory ProviderUpdate.fromJson(Map<String, dynamic> json) {
    return ProviderUpdate(
      name: json['name'] as String?,
      slug: json['slug'] as String?,
      type: json['type'] as String?,
      status: json['status'] as String?,
      serviceCategories: json['service_categories'] as String?,
      contactName: json['contact_name'] as String?,
      email: json['email'] as String?,
      whatsappPhone: json['whatsapp_phone'] as String?,
      locationLabel: json['location_label'] as String?,
      capacityNotes: json['capacity_notes'] as String?,
      operationalNotes: json['operational_notes'] as String?,
      tariffNotes: json['tariff_notes'] as String?,
      sourceNotes: json['source_notes'] as String?,
      isActive: json['is_active'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'slug': slug,
    'type': type,
    'status': status,
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
