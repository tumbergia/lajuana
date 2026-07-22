import 'dart:math';

import 'package:mobile_domain/src/providers/provider_list_item.dart';
import 'package:mobile_domain/src/providers/providers_repository.dart';
import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/providers/infrastructure/local/providers_database.dart';
import 'package:mobile/features/providers/infrastructure/local/providers_local_data_source.dart';
import 'package:mobile/features/providers/infrastructure/remote/providers_api_client.dart';

/// Repositorio de proveedores offline-first.
///
/// Lecturas: remoto → cache SQLite → fallback local.
/// Escrituras: local-first + shared outbox.
class ProvidersRepositoryImpl implements ProvidersRepository {
  ProvidersRepositoryImpl({
    required ProvidersApiClient apiClient,
    required OutboxRepository outbox,
    ProvidersDatabase? database,
  })  : _apiClient = apiClient,
        _outbox = outbox,
        _local = ProvidersLocalDataSource(
          database: database ?? ProvidersDatabase.instance,
        ) {
    _outbox.registerHandler(
      _entityType,
      OutboxEntityHandler(
        onApplied: _onApplied,
        onFailed: _onFailed,
      ),
    );
  }

  static const String _entityType = 'provider';

  final ProvidersApiClient _apiClient;
  final OutboxRepository _outbox;
  final ProvidersLocalDataSource _local;
  final Random _random = Random();

  @override
  Future<List<ProviderListItem>> listProviders({
    bool includeDeleted = false,
  }) async {
    try {
      final items = await _apiClient.listProviders(includeDeleted: true);
      await _local.upsertAll(items);
    } catch (_) {
      // Sin red: servir cache local.
    }
    return _local.listAll(includeDeleted: includeDeleted);
  }

  @override
  Future<ProviderListItem> getProviderById(String providerId) async {
    try {
      final item = await _apiClient.getProviderById(providerId);
      await _local.upsert(item);
      return item;
    } catch (_) {
      final cached = await _local.getById(providerId);
      if (cached == null) rethrow;
      return cached;
    }
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
    final localId = _nextLocalId();
    final payload = _buildPayload(
      name: name,
      slug: _slugify(name),
      type: type,
      status: status,
      serviceCategories: serviceCategories ?? const [],
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

    final localItem = ProviderListItem(
      id: localId,
      name: name,
      slug: _slugify(name),
      type: type,
      status: status,
      serviceCategories: serviceCategories ?? const [],
      contactName: contactName,
      email: email,
      whatsappPhone: whatsappPhone,
      locationLabel: locationLabel,
      isActive: isActive,
    );
    await _local.upsert(localItem, syncStatus: 'pending');

    await _outbox.enqueue(
      entityType: _entityType,
      operationType: 'create',
      entityLocalId: localId,
      payload: payload,
    );

    return localItem;
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
    final cached = await _local.getById(providerId);
    if (cached == null) {
      // Sin copia local: intento en caliente.
      final payload = _buildPayload(
        name: name,
        type: type,
        status: status,
        serviceCategories: serviceCategories ?? const [],
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
      await _local.upsert(item);
      return item;
    }

    final merged = _mergeItem(cached,
      name: name,
      type: type,
      status: status,
      serviceCategories: serviceCategories ?? const [],
      contactName: contactName,
      email: email,
      whatsappPhone: whatsappPhone,
      locationLabel: locationLabel,
      isActive: isActive,
    );
    await _local.upsert(merged, syncStatus: 'pending');

    await _outbox.enqueue(
      entityType: _entityType,
      operationType: 'update',
      entityLocalId: providerId,
      entityRemoteId: providerId,
      payload: _buildPayload(
        name: name,
        type: type,
        status: status,
        serviceCategories: serviceCategories ?? const [],
        contactName: contactName,
        email: email,
        whatsappPhone: whatsappPhone,
        locationLabel: locationLabel,
        capacityNotes: capacityNotes,
        operationalNotes: operationalNotes,
        tariffNotes: tariffNotes,
        sourceNotes: sourceNotes,
        isActive: isActive,
      ),
    );

    return merged;
  }

  @override
  Future<void> deactivateProvider(String providerId) async {
    final cached = await _local.getById(providerId);
    if (cached == null) {
      await _apiClient.deactivateProvider(providerId);
      return;
    }
    final updated = ProviderListItem(
      id: cached.id,
      name: cached.name,
      slug: cached.slug,
      type: cached.type,
      status: 'inactive',
      serviceCategories: cached.serviceCategories,
      contactName: cached.contactName,
      email: cached.email,
      whatsappPhone: cached.whatsappPhone,
      locationLabel: cached.locationLabel,
      isActive: false,
    );
    await _local.upsert(updated, syncStatus: 'pending');

    await _outbox.enqueue(
      entityType: _entityType,
      operationType: 'deactivate',
      entityLocalId: providerId,
      entityRemoteId: providerId,
      payload: {'status': 'inactive', 'is_active': false},
    );
  }

  @override
  Future<ProviderListItem> reactivateProvider(String providerId) async {
    final cached = await _local.getById(providerId);
    if (cached == null) {
      return updateProvider(
        providerId: providerId,
        status: 'active',
        isActive: true,
      );
    }
    final updated = ProviderListItem(
      id: cached.id,
      name: cached.name,
      slug: cached.slug,
      type: cached.type,
      status: 'active',
      serviceCategories: cached.serviceCategories,
      contactName: cached.contactName,
      email: cached.email,
      whatsappPhone: cached.whatsappPhone,
      locationLabel: cached.locationLabel,
      isActive: true,
    );
    await _local.upsert(updated, syncStatus: 'pending');

    await _outbox.enqueue(
      entityType: _entityType,
      operationType: 'reactivate',
      entityLocalId: providerId,
      entityRemoteId: providerId,
      payload: {'status': 'active', 'is_active': true},
    );

    return updated;
  }

  // ── Outbox handlers ──

  Future<void> _onApplied(OutboxApplied applied) async {
    await _local.markSynced(
      applied.entityLocalId,
      remoteId: applied.entityRemoteId,
      version: applied.version,
    );
  }

  Future<void> _onFailed(OutboxFailed failed) async {
    await _local.markFailed(
      failed.entityLocalId,
      failed.status,
      error: failed.errorMessage,
    );
  }

  // ── Helpers ──

  ProviderListItem _mergeItem(
    ProviderListItem current, {
    String? name,
    String? type,
    String? status,
    List<String>? serviceCategories,
    String? contactName,
    String? email,
    String? whatsappPhone,
    String? locationLabel,
    bool? isActive,
  }) {
    return ProviderListItem(
      id: current.id,
      name: name ?? current.name,
      slug: current.slug,
      type: type ?? current.type,
      status: status ?? current.status,
      serviceCategories: serviceCategories ?? current.serviceCategories,
      contactName: contactName ?? current.contactName,
      email: email ?? current.email,
      whatsappPhone: whatsappPhone ?? current.whatsappPhone,
      locationLabel: locationLabel ?? current.locationLabel,
      isActive: isActive ?? current.isActive,
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

  String _slugify(String name) {
    return name
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9\s-]'), '')
        .replaceAll(RegExp(r'\s+'), '-')
        .replaceAll(RegExp(r'-+'), '-')
        .trim()
        .replaceAll(RegExp(r'^-|-$'), '');
  }

  String _nextLocalId() {
    final stamp = DateTime.now().toUtc().microsecondsSinceEpoch;
    final suffix = _random.nextInt(999999).toString().padLeft(6, '0');
    return 'local-provider-$stamp-$suffix';
  }
}
