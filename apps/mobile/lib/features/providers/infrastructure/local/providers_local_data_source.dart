import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'package:mobile_domain/src/providers/provider_list_item.dart';
import 'package:mobile/features/providers/infrastructure/local/providers_database.dart';

/// Acceso a la tabla local de providers.
class ProvidersLocalDataSource {
  ProvidersLocalDataSource({required ProvidersDatabase database})
    : _db = database;

  final ProvidersDatabase _db;

  Future<List<ProviderListItem>> listAll({bool includeDeleted = false}) async {
    final db = await _db.database;
    final where = includeDeleted ? null : 'deleted_at IS NULL';
    final rows = await db.query(
      'providers_local',
      where: where,
      orderBy: 'name ASC',
    );
    return rows.map(_rowToItem).toList(growable: false);
  }

  Future<ProviderListItem?> getById(String id) async {
    final db = await _db.database;
    final rows = await db.query(
      'providers_local',
      where: 'id = ? OR remote_id = ?',
      whereArgs: [id, id],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return _rowToItem(rows.first);
  }

  Future<void> upsertAll(List<ProviderListItem> items) async {
    final db = await _db.database;
    final batch = db.batch();
    for (final item in items) {
      batch.insert(
        'providers_local',
        _itemToRow(item, syncStatus: 'synced'),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<void> upsert(
    ProviderListItem item, {
    String syncStatus = 'synced',
  }) async {
    final db = await _db.database;
    await db.insert(
      'providers_local',
      _itemToRow(item, syncStatus: syncStatus),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> markSynced(
    String localId, {
    String? remoteId,
    int? version,
  }) async {
    final db = await _db.database;
    final values = <String, dynamic>{
      'sync_status': 'synced',
      'sync_error': null,
    };
    if (remoteId != null) values['remote_id'] = remoteId;
    if (version != null) values['version_remote'] = version;
    await db.update(
      'providers_local',
      values,
      where: 'id = ?',
      whereArgs: [localId],
    );
  }

  Future<void> markFailed(
    String localId,
    String status, {
    String? error,
  }) async {
    final db = await _db.database;
    await db.update(
      'providers_local',
      {'sync_status': status, 'sync_error': error},
      where: 'id = ?',
      whereArgs: [localId],
    );
  }

  Future<void> deleteLocal(String id) async {
    final db = await _db.database;
    await db.delete('providers_local', where: 'id = ?', whereArgs: [id]);
  }

  Future<void> clearAll() async {
    final db = await _db.database;
    await db.delete('providers_local');
  }

  ProviderListItem _rowToItem(Map<String, Object?> row) {
    final serviceCategoriesRaw = row['service_categories'] as String?;
    return ProviderListItem(
      id: (row['remote_id'] as String?) ?? (row['id'] as String),
      name: row['name'] as String? ?? '',
      slug: row['slug'] as String? ?? '',
      type: row['type'] as String? ?? '',
      status: row['status'] as String? ?? 'active',
      serviceCategories: serviceCategoriesRaw != null
          ? (jsonDecode(serviceCategoriesRaw) as List<dynamic>)
                .map((e) => e as String)
                .toList(growable: false)
          : const [],
      contactName: row['contact_name'] as String?,
      email: row['email'] as String?,
      whatsappPhone: row['whatsapp_phone'] as String?,
      locationLabel: row['location_label'] as String?,
      isActive: (row['is_active'] as int?) == 1,
    );
  }

  Map<String, dynamic> _itemToRow(
    ProviderListItem item, {
    required String syncStatus,
  }) {
    return {
      'id': item.id,
      'remote_id': item.id,
      'name': item.name,
      'slug': item.slug,
      'type': item.type,
      'status': item.status,
      'service_categories': item.serviceCategories.isEmpty
          ? null
          : jsonEncode(item.serviceCategories),
      'contact_name': item.contactName,
      'email': item.email,
      'whatsapp_phone': item.whatsappPhone,
      'location_label': item.locationLabel,
      'is_active': item.isActive ? 1 : 0,
      'deleted_at': null,
      'sync_status': syncStatus,
      'sync_error': null,
      'version_remote': null,
      'updated_at_remote': null,
    };
  }
}
