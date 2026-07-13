import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite/sqflite.dart';
import 'package:workmanager/workmanager.dart';

const notificationBackgroundTaskName = 'lajuana.notifications.poll';
const _lastSeenKey = 'notifications.last_seen_id';
const _apiBaseUrlKey = 'notifications.api_base_url';
const _backgroundEnabledKey = 'notifications.background_enabled';

/// Background polling + local notifications (Android/iOS). No-op elsewhere.
class NotificationBackgroundService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  /// Workmanager and local notifications are only supported on Android/iOS.
  static bool get supportsBackgroundNotifications {
    if (kIsWeb) return false;
    return Platform.isAndroid || Platform.isIOS;
  }

  static Future<void> initialize() async {
    if (!supportsBackgroundNotifications) return;
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings();
    await _plugin.initialize(
      const InitializationSettings(android: android, iOS: ios),
    );
    await Workmanager().initialize(notificationCallbackDispatcher);
  }

  static Future<void> persistApiBaseUrl(String baseUrl) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_apiBaseUrlKey, baseUrl);
  }

  static Future<void> setEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_backgroundEnabledKey, enabled);
  }

  static Future<bool> isEnabled() async {
    if (!supportsBackgroundNotifications) return false;
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_backgroundEnabledKey) ?? true;
  }

  static Future<void> registerPeriodic() async {
    if (!supportsBackgroundNotifications) return;
    await setEnabled(true);
    await Workmanager().registerPeriodicTask(
      notificationBackgroundTaskName,
      notificationBackgroundTaskName,
      frequency: const Duration(minutes: 15),
      existingWorkPolicy: ExistingPeriodicWorkPolicy.keep,
      constraints: Constraints(networkType: NetworkType.connected),
    );
  }

  static Future<void> cancel() async {
    if (!supportsBackgroundNotifications) {
      await setEnabled(false);
      return;
    }
    await setEnabled(false);
    await Workmanager().cancelByUniqueName(notificationBackgroundTaskName);
  }

  static Future<void> showLocal({
    required String title,
    required String body,
    int id = 0,
  }) async {
    if (!supportsBackgroundNotifications) return;
    const android = AndroidNotificationDetails(
      'lajuana_in_app',
      'Notificaciones La Juana',
      channelDescription: 'Alertas operativas in-app',
      importance: Importance.high,
      priority: Priority.high,
    );
    const details = NotificationDetails(
      android: android,
      iOS: DarwinNotificationDetails(),
    );
    await _plugin.show(id, title, body, details);
  }
}

@pragma('vm:entry-point')
void notificationCallbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    if (task != notificationBackgroundTaskName) return Future.value(true);
    try {
      await _pollAndNotify();
    } catch (_) {
      // Swallow background errors; next tick will retry.
    }
    return Future.value(true);
  });
}

Future<void> _pollAndNotify() async {
  final prefs = await SharedPreferences.getInstance();
  if (!(prefs.getBool(_backgroundEnabledKey) ?? true)) return;

  final baseUrl = prefs.getString(_apiBaseUrlKey);
  if (baseUrl == null || baseUrl.isEmpty) return;

  final token = await _readAccessTokenFromSqlite();
  if (token == null || token.isEmpty) return;

  final uri = Uri.parse('$baseUrl/notifications/in-app?unread_only=true&limit=20');
  final response = await http.get(
    uri,
    headers: {
      HttpHeaders.authorizationHeader: 'Bearer $token',
      HttpHeaders.contentTypeHeader: 'application/json',
    },
  ).timeout(const Duration(seconds: 20));
  if (response.statusCode < 200 || response.statusCode >= 300) return;

  final decoded = jsonDecode(response.body);
  if (decoded is! List || decoded.isEmpty) return;

  final lastSeen = prefs.getString(_lastSeenKey);
  final items = decoded.whereType<Map>().toList();
  final fresh = <Map>[];
  for (final item in items) {
    final id = item['id']?.toString();
    if (id == null) continue;
    if (lastSeen != null && id == lastSeen) break;
    fresh.add(item);
  }
  if (fresh.isEmpty) return;

  if (fresh.length == 1) {
    final item = fresh.first;
    await NotificationBackgroundService.showLocal(
      title: item['title']?.toString() ?? 'Nueva notificación',
      body: item['body']?.toString() ?? '',
      id: item['id'].hashCode,
    );
  } else {
    await NotificationBackgroundService.showLocal(
      title: '${fresh.length} notificaciones nuevas',
      body: fresh
          .take(3)
          .map((item) => item['title']?.toString() ?? '')
          .where((t) => t.isNotEmpty)
          .join(' · '),
      id: DateTime.now().millisecondsSinceEpoch ~/ 1000,
    );
  }

  final newestId = items.first['id']?.toString();
  if (newestId != null) {
    await prefs.setString(_lastSeenKey, newestId);
  }
}

Future<String?> _readAccessTokenFromSqlite() async {
  try {
    final dbPath = await getDatabasesPath();
    final path = '$dbPath/la_juana_auth_v1.db';
    if (!await File(path).exists()) return null;
    final db = await openDatabase(path, readOnly: true);
    try {
      final rows = await db.query(
        'session_local',
        columns: ['access_token'],
        limit: 1,
      );
      if (rows.isEmpty) return null;
      return rows.first['access_token'] as String?;
    } finally {
      await db.close();
    }
  } catch (_) {
    return null;
  }
}
