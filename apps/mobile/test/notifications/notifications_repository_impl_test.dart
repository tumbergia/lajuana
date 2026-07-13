import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mobile/features/notifications/domain/notifications_repository.dart';
import 'package:mobile/features/notifications/infrastructure/notifications_api_client.dart';
import 'package:mobile_domain/src/gen/in_app_notification.dart';
import 'package:mobile_domain/src/gen/notification_preferences.dart';

void main() {
  test('repository listInApp parses payload', () async {
    final client = MockClient((request) async {
      expect(request.url.path, endsWith('/notifications/in-app'));
      return http.Response(
        jsonEncode([
          {
            'id': 'n1',
            'user_id': 'u1',
            'reservation_id': null,
            'title': 'Hola',
            'body': 'Mundo',
            'read': false,
            'event_type': 'human_review_requested',
            'version': 1,
            'created_at': '2026-07-13T12:00:00Z',
            'updated_at': '2026-07-13T12:00:00Z',
            'deleted_at': null,
          },
        ]),
        200,
        headers: {'content-type': 'application/json'},
      );
    });

    final api = NotificationsApiClient(
      baseUrl: 'http://localhost/api/v1',
      readAccessToken: () async => 'token',
      refreshSession: () async => false,
      httpClient: client,
    );
    final repo = NotificationsRepositoryImpl(apiClient: api);
    final items = await repo.listInApp();
    expect(items, hasLength(1));
    expect(items.first, isA<InAppNotification>());
    expect(items.first.reservationId, isNull);
    expect(items.first.title, 'Hola');
  });

  test('repository preferences roundtrip', () async {
    final client = MockClient((request) async {
      if (request.method == 'GET') {
        return http.Response(
          jsonEncode({
            'preferences': {'reservation_created': true},
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      expect(request.method, 'PUT');
      return http.Response(
        jsonEncode({
          'preferences': {'reservation_created': false},
        }),
        200,
        headers: {'content-type': 'application/json'},
      );
    });

    final api = NotificationsApiClient(
      baseUrl: 'http://localhost/api/v1',
      readAccessToken: () async => 'token',
      refreshSession: () async => false,
      httpClient: client,
    );
    final repo = NotificationsRepositoryImpl(apiClient: api);
    final prefs = await repo.getPreferences();
    expect(prefs, isA<NotificationPreferences>());
    final updated = await repo.updatePreferences({
      'reservation_created': false,
    });
    expect(updated.preferences?['reservation_created'], isFalse);
  });

  test('repository clearInbox and deleteOne hit DELETE endpoints', () async {
    final paths = <String>[];
    final client = MockClient((request) async {
      paths.add('${request.method} ${request.url.path}${request.url.query.isEmpty ? '' : '?${request.url.query}'}');
      return http.Response(
        jsonEncode({'cleared_count': 2}),
        200,
        headers: {'content-type': 'application/json'},
      );
    });

    final api = NotificationsApiClient(
      baseUrl: 'http://localhost/api/v1',
      readAccessToken: () async => 'token',
      refreshSession: () async => false,
      httpClient: client,
    );
    final repo = NotificationsRepositoryImpl(apiClient: api);

    expect(await repo.clearInbox(readOnly: true), 2);
    expect(await repo.deleteOne('n1'), 2);
    expect(paths, [
      'DELETE /api/v1/notifications/in-app?read_only=true',
      'DELETE /api/v1/notifications/in-app/n1',
    ]);
  });
}
