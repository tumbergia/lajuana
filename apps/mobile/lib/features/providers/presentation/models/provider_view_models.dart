import 'package:mobile_ui/src/widgets/app_badge.dart';

class ProviderRecord {
  const ProviderRecord({
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

  bool get isInactive => !isActive || status == 'inactive';

  String get typeLabel => providerTypeLabel(type);

  String get statusLabel => providerStatusLabel(status);

  AppBadgeTone get statusTone {
    if (!isActive || status == 'inactive') return AppBadgeTone.neutral;
    return switch (status) {
      'active' => AppBadgeTone.success,
      'needs_review' => AppBadgeTone.warning,
      'blocked' => AppBadgeTone.danger,
      _ => AppBadgeTone.primary,
    };
  }

  String get subtitle {
    final parts = <String>[
      typeLabel,
      if (locationLabel != null && locationLabel!.isNotEmpty) locationLabel!,
    ];
    return parts.join(' · ');
  }
}

String providerTypeLabel(String type) {
  return switch (type) {
    'lodging' => 'Alojamiento',
    'food' => 'Alimentacion',
    'transport_people' => 'Transporte pasajeros',
    'equine_transport' => 'Transporte mulas',
    'experience_ally' => 'Aliado experiencia',
    'guide_ally' => 'Guia aliado',
    'park_or_access' => 'Parque / acceso',
    'insurance' => 'Seguro',
    _ => 'Otro',
  };
}

String providerStatusLabel(String status) {
  return switch (status) {
    'active' => 'Activo',
    'inactive' => 'Inactivo',
    'needs_review' => 'Revision',
    'blocked' => 'Bloqueado',
    _ => 'Estado desconocido',
  };
}

const providerTypeOptions = <String, String>{
  'lodging': 'Alojamiento',
  'food': 'Alimentacion',
  'transport_people': 'Transporte pasajeros',
  'equine_transport': 'Transporte mulas',
  'experience_ally': 'Aliado experiencia',
  'guide_ally': 'Guia aliado',
  'park_or_access': 'Parque / acceso',
  'insurance': 'Seguro',
  'other': 'Otro',
};

const providerStatusOptions = <String, String>{
  'active': 'Activo',
  'inactive': 'Inactivo',
  'needs_review': 'Revision',
  'blocked': 'Bloqueado',
};
