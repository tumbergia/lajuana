import 'package:mobile/app/sync/outbox_repository.dart';
import 'package:mobile/features/notifications/infrastructure/local/notifications_database.dart';
import 'package:mobile/features/notifications/infrastructure/local/notifications_local_data_source.dart';
import 'package:mobile/features/notifications/infrastructure/notifications_api_client.dart';
import 'package:mobile_domain/src/gen/in_app_notification.dart';
import 'package:mobile_domain/src/gen/notification_preferences.dart';

abstract class NotificationsRepository {
  Future<List<InAppNotification>> listInApp({
    int limit = 50,
    String? beforeId,
    bool unreadOnly = false,
  });

  Future<int> unreadCount();

  Future<InAppNotification> markRead(String notificationId);

  Future<void> markAllRead();

  Future<int> deleteOne(String notificationId);

  Future<int> clearInbox({bool readOnly = false});

  Future<NotificationPreferences> getPreferences();

  Future<NotificationPreferences> updatePreferences(
    Map<String, bool> preferences,
  );

  /// Envía un mensaje de WhatsApp directamente vía API.
  Future<void> sendWhatsAppMessage({
    required String phone,
    required String message,
  });
}

/// Repositorio de notificaciones offline-first.
///
/// Lecturas: cache-first con fallback a SQLite.
/// Escrituras: optimistas locales + outbox compartido.
class NotificationsRepositoryImpl implements NotificationsRepository {
  NotificationsRepositoryImpl({
    required NotificationsApiClient apiClient,
    OutboxRepository? outbox,
    NotificationsDatabase? database,
  })  : _api = apiClient,
        _outbox = outbox,
        _local = database != null
            ? NotificationsLocalDataSource(database: database)
            : null {
    _outbox?.registerHandler(
      _entityType,
      OutboxEntityHandler(
        onApplied: _onApplied,
        onFailed: _onFailed,
      ),
    );
  }

  static const String _entityType = 'notification_mutation';

  final NotificationsApiClient _api;
  final OutboxRepository? _outbox;
  final NotificationsLocalDataSource? _local;

  @override
  Future<List<InAppNotification>> listInApp({
    int limit = 50,
    String? beforeId,
    bool unreadOnly = false,
  }) async {
    try {
      final items = await _api.listInApp(
        limit: limit,
        beforeId: beforeId,
        unreadOnly: unreadOnly,
      );
      await _local?.cacheList(items);
      return items;
    } catch (_) {
      if (_local == null) rethrow;
      return _local!.listAll(
        limit: limit,
        beforeId: beforeId,
        unreadOnly: unreadOnly,
      );
    }
  }

  @override
  Future<int> unreadCount() async {
    try {
      final count = await _api.unreadCount();
      await _local?.cacheUnreadCount(count);
      return count;
    } catch (_) {
      if (_local == null) rethrow;
      return _local!.unreadCount();
    }
  }

  @override
  Future<InAppNotification> markRead(String notificationId) async {
    await _local?.markRead(notificationId);
    await _outbox?.enqueue(
      entityType: _entityType,
      operationType: 'mark_read',
      entityLocalId: notificationId,
      payload: {},
    );
    try {
      return await _api.markRead(notificationId);
    } catch (_) {
      return InAppNotification(
        id: notificationId,
        version: 0,
        userId: '',
        title: '',
        body: '',
        read: true,
        eventType: '',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );
    }
  }

  @override
  Future<void> markAllRead() async {
    await _local?.markAllRead();
    await _outbox?.enqueue(
      entityType: _entityType,
      operationType: 'mark_all_read',
      entityLocalId: '__all__',
      payload: {},
    );
    try {
      await _api.markAllRead();
    } catch (_) {
      // Best-effort — local state already updated.
    }
  }

  @override
  Future<int> deleteOne(String notificationId) async {
    await _local?.markDeleted(notificationId);
    await _outbox?.enqueue(
      entityType: _entityType,
      operationType: 'delete',
      entityLocalId: notificationId,
      payload: {},
    );
    // Best-effort: try API, return cached count or optimistic 1.
    try {
      return await _api.deleteOne(notificationId);
    } catch (_) {
      return 1;
    }
  }

  @override
  Future<int> clearInbox({bool readOnly = false}) async {
    await _local?.clearAll(readOnly: readOnly);
    await _outbox?.enqueue(
      entityType: _entityType,
      operationType: 'clear_inbox',
      entityLocalId: '__all__',
      payload: {'read_only': readOnly},
    );
    try {
      return await _api.clearInbox(readOnly: readOnly);
    } catch (_) {
      return 0;
    }
  }

  @override
  Future<NotificationPreferences> getPreferences() async {
    try {
      final prefs = await _api.getPreferences();
      if (prefs.preferences != null) {
        await _local?.savePreferences(prefs.preferences!);
      }
      return prefs;
    } catch (_) {
      final cached = await _local?.getPreferences();
      return cached ?? const NotificationPreferences();
    }
  }

  @override
  Future<NotificationPreferences> updatePreferences(
    Map<String, bool> preferences,
  ) async {
    await _local?.savePreferences(preferences);
    try {
      return await _api.updatePreferences(preferences);
    } catch (_) {
      // Keep local update, will sync via next online call
      return NotificationPreferences(preferences: preferences);
    }
  }

  @override
  Future<void> sendWhatsAppMessage({
    required String phone,
    required String message,
  }) async {
    // WhatsApp messages are inherently online — no offline queue.
    await _api.sendWhatsAppMessage(phone: phone, message: message);
  }

  // ── Outbox handlers ──

  Future<void> _onApplied(OutboxApplied applied) async {
    // For mark_read, delete, clear_inbox: confirm sync.
    await _local?.markSynced(applied.entityLocalId);
  }

  Future<void> _onFailed(OutboxFailed failed) async {
    // TODO: handle conflict/rejected — for now, leave as pending.
  }
}
