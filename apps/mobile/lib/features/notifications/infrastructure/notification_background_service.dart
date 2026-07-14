import 'dart:convert';
import 'dart:io';
import 'dart:ui';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'package:mobile/features/notifications/presentation/notification_content.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite/sqflite.dart';
import 'package:workmanager/workmanager.dart';

const notificationBackgroundTaskName = 'lajuana.notifications.poll';
const _lastSeenKey = 'notifications.last_seen_id';
const _apiBaseUrlKey = 'notifications.api_base_url';
const _backgroundEnabledKey = 'notifications.background_enabled';
const _androidChannelId = 'lajuana_in_app';
const _androidChannelName = 'Notificaciones La Juana';
const _androidChannelDescription = 'Alertas operativas in-app';

/// Background polling + local notifications (Android/iOS). No-op elsewhere.
class NotificationBackgroundService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  static bool _pluginReady = false;

  /// Workmanager and local notifications are only supported on Android/iOS.
  static bool get supportsBackgroundNotifications {
    if (kIsWeb) return false;
    return Platform.isAndroid || Platform.isIOS;
  }

  static Future<void> initialize() async {
    if (!supportsBackgroundNotifications) return;
    await _ensurePluginInitialized();
    await requestPermissions();
    await Workmanager().initialize(notificationCallbackDispatcher);
  }

  /// Lightweight init for Workmanager isolates (no Workmanager re-register).
  static Future<void> initializeForBackgroundIsolate() async {
    if (!supportsBackgroundNotifications) return;
    WidgetsFlutterBinding.ensureInitialized();
    DartPluginRegistrant.ensureInitialized();
    await _ensurePluginInitialized();
  }

  static Future<void> _ensurePluginInitialized() async {
    if (_pluginReady) return;
    // Small icons must be a white alpha mask on transparent — not the launcher.
    // Prefer @drawable/ic_notification; fall back if the resource was stripped.
    var defaultIcon = '@drawable/ic_notification';
    try {
      await _initializeWithIcon(defaultIcon);
    } catch (error, stack) {
      debugPrint(
        'Notification init with ic_notification failed: $error\n$stack',
      );
      defaultIcon = '@mipmap/ic_launcher';
      await _initializeWithIcon(defaultIcon);
    }
    await _ensureAndroidChannel();
    _pluginReady = true;
  }

  static Future<void> _initializeWithIcon(String defaultIcon) async {
    final android = AndroidInitializationSettings(defaultIcon);
    const ios = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    await _plugin.initialize(
      InitializationSettings(android: android, iOS: ios),
    );
  }

  static Future<void> _ensureAndroidChannel() async {
    if (!Platform.isAndroid) return;
    final android = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    await android?.createNotificationChannel(
      const AndroidNotificationChannel(
        _androidChannelId,
        _androidChannelName,
        description: _androidChannelDescription,
        importance: Importance.high,
      ),
    );
  }

  /// Android 13+ / iOS: prompt for notification permission when needed.
  static Future<bool> requestPermissions() async {
    if (!supportsBackgroundNotifications) return false;
    if (Platform.isAndroid) {
      final android = _plugin.resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>();
      final granted = await android?.requestNotificationsPermission();
      return granted ?? false;
    }
    if (Platform.isIOS) {
      final ios = _plugin.resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin>();
      final granted = await ios?.requestPermissions(
        alert: true,
        badge: true,
        sound: true,
      );
      return granted ?? false;
    }
    return false;
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

  /// Persist newest seen id so background polling does not re-notify.
  static Future<void> markLastSeenId(String? notificationId) async {
    if (!supportsBackgroundNotifications) return;
    if (notificationId == null || notificationId.isEmpty) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_lastSeenKey, notificationId);
    } catch (error, stack) {
      if (kDebugMode) {
        debugPrint('markLastSeenId failed: $error\n$stack');
      }
    }
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
    try {
      await _ensurePluginInitialized();
      await _plugin.show(
        id,
        title,
        body,
        _notificationDetails(icon: '@drawable/ic_notification'),
      );
    } catch (error, stack) {
      debugPrint('showLocal failed with ic_notification: $error\n$stack');
      // Release shrinker can strip Dart-only drawables; fall back so alerts still fire.
      try {
        await _plugin.show(
          id,
          title,
          body,
          _notificationDetails(icon: '@mipmap/ic_launcher'),
        );
      } catch (fallbackError, fallbackStack) {
        debugPrint('showLocal fallback failed: $fallbackError\n$fallbackStack');
      }
    }
  }

  static NotificationDetails _notificationDetails({required String icon}) {
    return NotificationDetails(
      android: AndroidNotificationDetails(
        _androidChannelId,
        _androidChannelName,
        channelDescription: _androidChannelDescription,
        icon: icon,
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: const DarwinNotificationDetails(),
    );
  }
}

@pragma('vm:entry-point')
void notificationCallbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    if (task != notificationBackgroundTaskName) return Future.value(true);
    try {
      await NotificationBackgroundService.initializeForBackgroundIsolate();
      await _pollAndNotify();
    } catch (error, stack) {
      if (kDebugMode) {
        debugPrint('Notification background poll failed: $error\n$stack');
      }
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
  final newestId = items.first['id']?.toString();

  // Cold start / first background run: seed cursor without notifying so the
  // existing unread inbox does not dump as "new" when opening the app.
  if (lastSeen == null || lastSeen.isEmpty) {
    await NotificationBackgroundService.markLastSeenId(newestId);
    return;
  }

  final fresh = <Map>[];
  for (final item in items) {
    final id = item['id']?.toString();
    if (id == null) continue;
    if (id == lastSeen) break;
    fresh.add(item);
  }
  if (fresh.isEmpty) return;

  final newest = fresh.first;
  final arrival = NotificationArrivalCopy.from(
    eventType: newest['event_type']?.toString() ?? '',
    title: newest['title']?.toString() ?? '',
    body: newest['body']?.toString() ?? '',
    contactPhone: newest['contact_phone']?.toString(),
    count: fresh.length,
  );
  await NotificationBackgroundService.showLocal(
    title: arrival.label,
    body: arrival.headline,
    id: fresh.length == 1
        ? newest['id'].hashCode
        : DateTime.now().millisecondsSinceEpoch ~/ 1000,
  );

  await NotificationBackgroundService.markLastSeenId(newestId);
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
