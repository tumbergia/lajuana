import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:mobile_domain/src/gen/in_app_clear_result.dart';
import 'package:mobile_domain/src/gen/in_app_notification.dart';
import 'package:mobile_domain/src/gen/in_app_unread_count.dart';
import 'package:mobile_domain/src/gen/notification_preferences.dart';
import 'package:mobile_domain/src/gen/notification_preferences_update.dart';

class NotificationsApiFailure implements Exception {
  const NotificationsApiFailure(this.message, {this.statusCode});
  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class NotificationsApiClient {
  NotificationsApiClient({
    required String baseUrl,
    required Future<String?> Function() readAccessToken,
    required Future<bool> Function() refreshSession,
    http.Client? httpClient,
  }) : _baseUrl = baseUrl,
       _readAccessToken = readAccessToken,
       _refreshSession = refreshSession,
       _http = httpClient ?? http.Client();

  final String _baseUrl;
  final Future<String?> Function() _readAccessToken;
  final Future<bool> Function() _refreshSession;
  final http.Client _http;

  Future<List<InAppNotification>> listInApp({
    int limit = 50,
    String? beforeId,
    bool unreadOnly = false,
  }) async {
    final params = <String>['limit=$limit'];
    if (beforeId != null && beforeId.isNotEmpty) {
      params.add('before_id=$beforeId');
    }
    if (unreadOnly) params.add('unread_only=true');
    final decoded = await _request('GET', '/notifications/in-app?${params.join('&')}');
    if (decoded is! List) {
      throw const NotificationsApiFailure('Payload inválido de notificaciones.');
    }
    return decoded
        .whereType<Map>()
        .map((item) => InAppNotification.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<int> unreadCount() async {
    final decoded = await _request('GET', '/notifications/in-app/unread-count');
    if (decoded is! Map) {
      throw const NotificationsApiFailure('Payload inválido de unread-count.');
    }
    return InAppUnreadCount.fromJson(Map<String, dynamic>.from(decoded)).unreadCount;
  }

  Future<InAppNotification> markRead(String notificationId) async {
    final decoded = await _request(
      'POST',
      '/notifications/in-app/$notificationId/read',
    );
    if (decoded is! Map) {
      throw const NotificationsApiFailure('Payload inválido al marcar leída.');
    }
    return InAppNotification.fromJson(Map<String, dynamic>.from(decoded));
  }

  Future<void> markAllRead() async {
    await _request('POST', '/notifications/in-app/read-all');
  }

  Future<int> deleteOne(String notificationId) async {
    final decoded = await _request(
      'DELETE',
      '/notifications/in-app/$notificationId',
    );
    if (decoded is! Map) {
      throw const NotificationsApiFailure('Payload inválido al eliminar.');
    }
    return InAppClearResult.fromJson(Map<String, dynamic>.from(decoded))
        .clearedCount;
  }

  Future<int> clearInbox({bool readOnly = false}) async {
    final query = readOnly ? '?read_only=true' : '';
    final decoded = await _request('DELETE', '/notifications/in-app$query');
    if (decoded is! Map) {
      throw const NotificationsApiFailure('Payload inválido al limpiar.');
    }
    return InAppClearResult.fromJson(Map<String, dynamic>.from(decoded))
        .clearedCount;
  }

  Future<NotificationPreferences> getPreferences() async {
    final decoded = await _request('GET', '/notifications/preferences');
    if (decoded is! Map) {
      throw const NotificationsApiFailure('Payload inválido de preferencias.');
    }
    return NotificationPreferences.fromJson(Map<String, dynamic>.from(decoded));
  }

  Future<NotificationPreferences> updatePreferences(
    Map<String, bool> preferences,
  ) async {
    final body = NotificationPreferencesUpdate(preferences: preferences).toJson();
    final decoded = await _request(
      'PUT',
      '/notifications/preferences',
      body: body,
    );
    if (decoded is! Map) {
      throw const NotificationsApiFailure('Payload inválido al guardar preferencias.');
    }
    return NotificationPreferences.fromJson(Map<String, dynamic>.from(decoded));
  }

  /// Envía un mensaje de WhatsApp directamente a través de la API.
  /// Usa el servicio outbound de WhatsApp del backend.
  Future<void> sendWhatsAppMessage({
    required String phone,
    required String message,
  }) async {
    await _request(
      'POST',
      '/whatsapp/send',
      body: {
        'to_phone': phone,
        'message': message,
      },
    );
  }

  Future<dynamic> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool retry = true,
  }) async {
    final token = await _readAccessToken();
    if (token == null || token.isEmpty) {
      throw const NotificationsApiFailure('La sesión expiró.');
    }
    final uri = Uri.parse('$_baseUrl$path');
    try {
      final headers = {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.authorizationHeader: 'Bearer $token',
      };
      late final http.Response response;
      switch (method) {
        case 'GET':
          response = await _http.get(uri, headers: headers).timeout(
            const Duration(seconds: 15),
          );
        case 'POST':
          response = await _http
              .post(
                uri,
                headers: headers,
                body: body == null ? null : jsonEncode(body),
              )
              .timeout(const Duration(seconds: 15));
        case 'PUT':
          response = await _http
              .put(
                uri,
                headers: headers,
                body: body == null ? null : jsonEncode(body),
              )
              .timeout(const Duration(seconds: 15));
        case 'DELETE':
          response = await _http
              .delete(uri, headers: headers)
              .timeout(const Duration(seconds: 15));
        default:
          throw NotificationsApiFailure('Método no soportado: $method');
      }
      if (response.statusCode == 401 && retry && await _refreshSession()) {
        return _request(method, path, body: body, retry: false);
      }
      if (response.statusCode < 200 || response.statusCode >= 300) {
        String message = 'Error de notificaciones (${response.statusCode}).';
        if (response.body.isNotEmpty) {
          try {
            final decoded = jsonDecode(response.body);
            if (decoded is Map && decoded['message'] is String) {
              message = decoded['message'] as String;
            }
          } catch (_) {}
        }
        throw NotificationsApiFailure(message, statusCode: response.statusCode);
      }
      if (response.body.isEmpty) return null;
      return jsonDecode(response.body);
    } on TimeoutException {
      throw const NotificationsApiFailure('Tiempo de espera agotado.');
    } on SocketException {
      throw const NotificationsApiFailure('Sin conexión.');
    }
  }
}
