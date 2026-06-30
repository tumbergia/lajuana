import 'package:mobile_domain/src/providers/provider_list_item.dart';
import 'package:mobile_domain/src/providers/providers_repository.dart';
import 'package:mobile/features/providers/infrastructure/mappers/provider_mapper.dart';
import 'package:mobile/features/providers/infrastructure/remote/providers_api_client.dart';

class ProvidersRepositoryImpl implements ProvidersRepository {
  ProvidersRepositoryImpl({required ProvidersApiClient apiClient})
      : _apiClient = apiClient;

  final ProvidersApiClient _apiClient;
  List<ProviderListItem>? _cachedItems;

  @override
  Future<List<ProviderListItem>> listProviders({
    bool includeDeleted = false,
  }) async {
    try {
      final items = await _apiClient.listProviders(
        includeDeleted: includeDeleted,
      );
      _cachedItems = items;
      return items;
    } catch (_) {
      if (_cachedItems != null) return _cachedItems!;
      rethrow;
    }
  }

  @override
  Future<ProviderListItem> getProviderById(String providerId) async {
    return _apiClient.getProviderById(providerId);
  }

  @override
  Future<ProviderListItem> createProvider({
    required String name,
    required String type,
    String status = 'active',
    List<String>? serviceCategories,
    String? contactName,
    String? email,
    String? whatsappPhone,
    String? locationLabel,
    String? capacityNotes,
    String? operationalNotes,
    String? tariffNotes,
    String? sourceNotes,
    bool isActive = true,
  }) async {
    final payload = _buildPayload(
      name: name,
      slug: slugifyProviderName(name),
      type: type,
      status: status,
      serviceCategories: serviceCategories,
      contactName: contactName,
      email: email,
      whatsappPhone: whatsappPhone,
      locationLabel: locationLabel,
      capacityNotes: capacityNotes,
      operationalNotes: operationalNotes,
      tariffNotes: tariffNotes,
      sourceNotes: sourceNotes,
      isActive: isActive,
    );
    final item = await _apiClient.createProvider(payload);
    final cached = _cachedItems;
    if (cached != null) {
      _cachedItems = [item, ...cached];
    }
    return item;
  }

  @override
  Future<ProviderListItem> updateProvider({
    required String providerId,
    String? name,
    String? type,
    String? status,
    List<String>? serviceCategories,
    String? contactName,
    String? email,
    String? whatsappPhone,
    String? locationLabel,
    String? capacityNotes,
    String? operationalNotes,
    String? tariffNotes,
    String? sourceNotes,
    bool? isActive,
  }) async {
    final payload = _buildPayload(
      name: name,
      type: type,
      status: status,
      serviceCategories: serviceCategories,
      contactName: contactName,
      email: email,
      whatsappPhone: whatsappPhone,
      locationLabel: locationLabel,
      capacityNotes: capacityNotes,
      operationalNotes: operationalNotes,
      tariffNotes: tariffNotes,
      sourceNotes: sourceNotes,
      isActive: isActive,
    );
    final item = await _apiClient.updateProvider(providerId, payload);
    final cached = _cachedItems;
    if (cached != null) {
      _cachedItems = cached
          .map((existing) => existing.id == providerId ? item : existing)
          .toList(growable: false);
    }
    return item;
  }

  @override
  Future<void> deactivateProvider(String providerId) async {
    await _apiClient.deactivateProvider(providerId);
    final cached = _cachedItems;
    if (cached != null) {
      _cachedItems = cached
          .map(
            (existing) => existing.id == providerId
                ? ProviderListItem(
                    id: existing.id,
                    name: existing.name,
                    slug: existing.slug,
                    type: existing.type,
                    status: 'inactive',
                    serviceCategories: existing.serviceCategories,
                    contactName: existing.contactName,
                    email: existing.email,
                    whatsappPhone: existing.whatsappPhone,
                    locationLabel: existing.locationLabel,
                    isActive: false,
                  )
                : existing,
          )
          .toList(growable: false);
    }
  }

  @override
  Future<ProviderListItem> reactivateProvider(String providerId) async {
    return updateProvider(
      providerId: providerId,
      status: 'active',
      isActive: true,
    );
  }

  Map<String, dynamic> _buildPayload({
    String? name,
    String? slug,
    String? type,
    String? status,
    List<String>? serviceCategories,
    String? contactName,
    String? email,
    String? whatsappPhone,
    String? locationLabel,
    String? capacityNotes,
    String? operationalNotes,
    String? tariffNotes,
    String? sourceNotes,
    bool? isActive,
  }) {
    final payload = <String, dynamic>{};
    if (name != null) payload['name'] = name;
    if (slug != null) payload['slug'] = slug;
    if (type != null) payload['type'] = type;
    if (status != null) payload['status'] = status;
    if (serviceCategories != null) {
      payload['service_categories'] = serviceCategories;
    }
    if (contactName != null) payload['contact_name'] = contactName;
    if (email != null) payload['email'] = email;
    if (whatsappPhone != null) payload['whatsapp_phone'] = whatsappPhone;
    if (locationLabel != null) payload['location_label'] = locationLabel;
    if (capacityNotes != null) payload['capacity_notes'] = capacityNotes;
    if (operationalNotes != null) {
      payload['operational_notes'] = operationalNotes;
    }
    if (tariffNotes != null) payload['tariff_notes'] = tariffNotes;
    if (sourceNotes != null) payload['source_notes'] = sourceNotes;
    if (isActive != null) payload['is_active'] = isActive;
    return payload;
  }
}
