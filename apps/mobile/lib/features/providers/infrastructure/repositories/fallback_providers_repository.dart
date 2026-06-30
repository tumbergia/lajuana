import 'package:mobile_domain/src/providers/provider_list_item.dart';
import 'package:mobile_domain/src/providers/providers_repository.dart';

class FallbackProvidersRepository implements ProvidersRepository {
  @override
  Future<List<ProviderListItem>> listProviders({
    bool includeDeleted = false,
  }) async {
    return const [];
  }

  @override
  Future<ProviderListItem> getProviderById(String providerId) async {
    throw Exception('ProvidersModule no inyectado');
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
    throw Exception('ProvidersModule no inyectado');
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
    throw Exception('ProvidersModule no inyectado');
  }

  @override
  Future<void> deactivateProvider(String providerId) async {
    throw Exception('ProvidersModule no inyectado');
  }

  @override
  Future<ProviderListItem> reactivateProvider(String providerId) async {
    throw Exception('ProvidersModule no inyectado');
  }
}
