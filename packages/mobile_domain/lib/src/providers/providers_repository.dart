import 'package:mobile_domain/src/providers/provider_list_item.dart';

abstract class ProvidersRepository {
  Future<List<ProviderListItem>> listProviders({bool includeDeleted = false});

  Future<ProviderListItem> getProviderById(String providerId);

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
  });

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
  });

  Future<void> deactivateProvider(String providerId);

  Future<ProviderListItem> reactivateProvider(String providerId);
}
