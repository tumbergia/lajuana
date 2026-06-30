import 'package:mobile_domain/src/providers/provider_list_item.dart';
import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';

String slugifyProviderName(String name) {
  final normalized = name.toLowerCase().trim();
  final slug = normalized
      .replaceAll(RegExp(r'[áàäâ]'), 'a')
      .replaceAll(RegExp(r'[éèëê]'), 'e')
      .replaceAll(RegExp(r'[íìïî]'), 'i')
      .replaceAll(RegExp(r'[óòöô]'), 'o')
      .replaceAll(RegExp(r'[úùüû]'), 'u')
      .replaceAll(RegExp(r'ñ'), 'n')
      .replaceAll(RegExp(r'[^a-z0-9]+'), '-')
      .replaceAll(RegExp(r'^-+|-+$'), '');
  return slug.isEmpty ? 'proveedor' : slug;
}

ProviderRecord listItemToRecord(ProviderListItem item) {
  return ProviderRecord(
    id: item.id,
    name: item.name,
    slug: item.slug,
    type: item.type,
    status: item.status,
    serviceCategories: item.serviceCategories,
    contactName: item.contactName,
    email: item.email,
    whatsappPhone: item.whatsappPhone,
    locationLabel: item.locationLabel,
    capacityNotes: item.capacityNotes,
    operationalNotes: item.operationalNotes,
    tariffNotes: item.tariffNotes,
    sourceNotes: item.sourceNotes,
    isActive: item.isActive,
  );
}
