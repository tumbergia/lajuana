class ProviderListItem {
  const ProviderListItem({
    required this.id,
    required this.name,
    required this.slug,
    required this.type,
    required this.status,
    this.serviceCategories = const [],
    this.contactName,
    this.email,
    this.whatsappPhone,
    this.locationLabel,
    this.capacityNotes,
    this.operationalNotes,
    this.tariffNotes,
    this.sourceNotes,
    this.isActive = true,
  });

  final String id;
  final String name;
  final String slug;
  final String type;
  final String status;
  final List<String> serviceCategories;
  final String? contactName;
  final String? email;
  final String? whatsappPhone;
  final String? locationLabel;
  final String? capacityNotes;
  final String? operationalNotes;
  final String? tariffNotes;
  final String? sourceNotes;
  final bool isActive;

  factory ProviderListItem.fromJson(Map<String, dynamic> json) {
    return ProviderListItem(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      slug: json['slug'] as String? ?? '',
      type: json['type'] as String? ?? 'other',
      status: json['status'] as String? ?? 'active',
      serviceCategories:
          (json['service_categories'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList(growable: false) ??
          const [],
      contactName: json['contact_name'] as String?,
      email: json['email'] as String?,
      whatsappPhone: json['whatsapp_phone'] as String?,
      locationLabel: json['location_label'] as String?,
      capacityNotes: json['capacity_notes'] as String?,
      operationalNotes: json['operational_notes'] as String?,
      tariffNotes: json['tariff_notes'] as String?,
      sourceNotes: json['source_notes'] as String?,
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}
