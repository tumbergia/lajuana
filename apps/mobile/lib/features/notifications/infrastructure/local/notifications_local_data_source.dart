import 'package:sqflite/sqflite.dart';

import 'package:mobile_domain/src/gen/in_app_notification.dart';
import 'package:mobile_domain/src/gen/notification_preferences.dart';
import 'package:mobile/features/notifications/infrastructure/local/notifications_database.dart';

/// Acceso local a la tabla de notificaciones.
class NotificationsLocalDataSource {
  NotificationsLocalDataSource({required NotificationsDatabase database})
    : _db = database;

  final NotificationsDatabase _db;

  Future<List<InAppNotification>> listAll({
    int limit = 50,
    String? beforeId,
    bool unreadOnly = false,
  }) async {
    final db = await _db.database;
    final where = <String>['deleted_at IS NULL'];
    final whereArgs = <Object?>[];
    if (unreadOnly) {
      where.add('read = 0');
    }
    if (beforeId != null) {
      where.add(
        'created_at < (SELECT created_at FROM notifications_local WHERE id = ?)',
      );
      whereArgs.add(beforeId);
    }
    final rows = await db.query(
      'notifications_local',
      where: where.join(' AND '),
      whereArgs: whereArgs,
      orderBy: 'created_at DESC',
      limit: limit,
    );
    return rows.map(_rowToNotification).toList(growable: false);
  }

  Future<int> unreadCount() async {
    final db = await _db.database;
    final rows = await db.query('notification_unread_count', limit: 1);
    if (rows.isEmpty) return 0;
    return rows.first['count'] as int? ?? 0;
  }

  Future<void> cacheList(List<InAppNotification> notifications) async {
    final db = await _db.database;
    final batch = db.batch();
    for (final n in notifications) {
      batch.insert(
        'notifications_local',
        _notificationToRow(n),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<void> cacheUnreadCount(int count) async {
    final db = await _db.database;
    await db.insert('notification_unread_count', {
      'id': 1,
      'count': count,
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<void> markRead(String notificationId) async {
    final db = await _db.database;
    await db.update(
      'notifications_local',
      {'read': 1, 'sync_status': 'pending'},
      where: 'id = ?',
      whereArgs: [notificationId],
    );
  }

  Future<void> markAllRead() async {
    final db = await _db.database;
    await db.update('notifications_local', {
      'read': 1,
      'sync_status': 'pending',
    }, where: 'read = 0 AND deleted_at IS NULL');
  }

  Future<void> markDeleted(String notificationId) async {
    final db = await _db.database;
    await db.update(
      'notifications_local',
      {
        'deleted_at': DateTime.now().toUtc().toIso8601String(),
        'sync_status': 'pending',
      },
      where: 'id = ?',
      whereArgs: [notificationId],
    );
  }

  Future<void> clearAll({bool readOnly = false}) async {
    final db = await _db.database;
    if (readOnly) {
      await db.update('notifications_local', {
        'deleted_at': DateTime.now().toUtc().toIso8601String(),
        'sync_status': 'pending',
      }, where: 'read = 1');
    } else {
      await db.update('notifications_local', {
        'deleted_at': DateTime.now().toUtc().toIso8601String(),
        'sync_status': 'pending',
      }, where: 'deleted_at IS NULL');
    }
  }

  Future<void> markSynced(String notificationId) async {
    final db = await _db.database;
    await db.update(
      'notifications_local',
      {'sync_status': 'synced', 'sync_error': null},
      where: 'id = ?',
      whereArgs: [notificationId],
    );
  }

  Future<NotificationPreferences?> getPreferences() async {
    final db = await _db.database;
    final rows = await db.query('notification_preferences_local');
    if (rows.isEmpty) return null;
    final map = <String, bool>{};
    for (final row in rows) {
      map[row['key'] as String] = (row['enabled'] as int) == 1;
    }
    return NotificationPreferences(preferences: map);
  }

  Future<void> savePreferences(Map<String, bool> preferences) async {
    final db = await _db.database;
    final batch = db.batch();
    for (final entry in preferences.entries) {
      batch.insert(
        'notification_preferences_local',
        {'key': entry.key, 'enabled': entry.value ? 1 : 0},
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  InAppNotification _rowToNotification(Map<String, Object?> row) {
    return InAppNotification(
      id: row['id'] as String,
      version: row['version'] as int? ?? 0,
      userId: row['user_id'] as String? ?? '',
      reservationId: row['reservation_id'] as String?,
      title: row['title'] as String? ?? '',
      body: row['body'] as String? ?? '',
      read: (row['read'] as int? ?? 0) == 1,
      eventType: row['event_type'] as String? ?? '',
      contactPhone: row['contact_phone'] as String?,
      createdAt:
          DateTime.tryParse(row['created_at'] as String? ?? '') ??
          DateTime.now(),
      updatedAt:
          DateTime.tryParse(row['updated_at'] as String? ?? '') ??
          DateTime.now(),
      deletedAt: row['deleted_at'] as String?,
    );
  }

  Map<String, dynamic> _notificationToRow(InAppNotification notification) {
    return {
      'id': notification.id,
      'version': notification.version,
      'user_id': notification.userId,
      'reservation_id': notification.reservationId,
      'title': notification.title,
      'body': notification.body,
      'read': notification.read ? 1 : 0,
      'event_type': notification.eventType,
      'contact_phone': notification.contactPhone,
      'created_at': notification.createdAt.toIso8601String(),
      'updated_at': notification.updatedAt.toIso8601String(),
      'deleted_at': notification.deletedAt,
      'sync_status': 'synced',
      'sync_error': null,
    };
  }
}
