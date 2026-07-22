import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:mobile/features/users/infrastructure/remote/users_api_client.dart';
import 'package:mobile/features/users/presentation/controllers/role_requests_controller.dart';
import 'package:mobile/features/users/presentation/controllers/users_list_controller.dart';

void main() {
  UsersApiClient buildClient(MockClientHandler handler) {
    return UsersApiClient(
      baseUrl: 'http://localhost/api/v1',
      readAccessToken: () async => 'token',
      refreshSession: () async => false,
      httpClient: MockClient(handler),
    );
  }

  group('UsersListController', () {
    test('loadInitial maps users and sets success', () async {
      final client = buildClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.path, '/api/v1/users');
        return http.Response(
          '''
[
  {
    "id": "u1",
    "email": "ana@example.com",
    "full_name": "Ana Guía",
    "role": "guide",
    "is_active": true,
    "version": 1,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
    "deleted_at": null
  }
]
''',
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final controller = UsersListController(apiClient: client);
      await controller.loadInitial();

      expect(controller.state, UsersLoadState.success);
      expect(controller.items, hasLength(1));
      expect(controller.items.first.fullName, 'Ana Guía');
      expect(controller.items.first.role, 'guide');
      controller.dispose();
    });

    test('createUser posts payload and refreshes list', () async {
      var createCalls = 0;
      var listCalls = 0;
      final client = buildClient((request) async {
        if (request.method == 'POST' && request.url.path == '/api/v1/users') {
          createCalls += 1;
          expect(request.body, contains('"role":"admin"'));
          return http.Response(
            '''
{
  "id": "u2",
  "email": "admin@example.com",
  "full_name": "Nuevo Admin",
  "role": "admin",
  "is_active": true,
  "version": 1,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "deleted_at": null
}
''',
            201,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.method == 'GET') {
          listCalls += 1;
          return http.Response(
            '''
[
  {
    "id": "u2",
    "email": "admin@example.com",
    "full_name": "Nuevo Admin",
    "role": "admin",
    "is_active": true,
    "version": 1,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
    "deleted_at": null
  }
]
''',
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('unexpected', 500);
      });

      final controller = UsersListController(apiClient: client);
      final created = await controller.createUser(
        email: 'admin@example.com',
        fullName: 'Nuevo Admin',
        password: 'SecurePass1',
        role: 'admin',
      );

      expect(created.role, 'admin');
      expect(createCalls, 1);
      expect(listCalls, 1);
      expect(controller.items.first.email, 'admin@example.com');
      controller.dispose();
    });
  });

  group('RoleRequestsController', () {
    test('createMyRequest stores pending request', () async {
      final client = buildClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, '/api/v1/role-requests');
        expect(request.body, contains('"requested_role":"guide"'));
        return http.Response(
          '''
{
  "id": "r1",
  "user_id": "u1",
  "user_email": "sinrol@example.com",
  "user_full_name": "Sin Rol",
  "user_role": "unassigned",
  "requested_role": "guide",
  "status": "pending",
  "decided_role": null,
  "decided_by": null,
  "decided_at": null,
  "note": null,
  "version": 1,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "deleted_at": null
}
''',
          201,
          headers: {'content-type': 'application/json'},
        );
      });

      final controller = RoleRequestsController(apiClient: client);
      final created = await controller.createMyRequest('guide');

      expect(created.status, 'pending');
      expect(controller.myRequest?.requestedRole, 'guide');
      controller.dispose();
    });

    test('decide approve refreshes pending list', () async {
      var decideCalls = 0;
      var listCalls = 0;
      final client = buildClient((request) async {
        if (request.method == 'POST' &&
            request.url.path.endsWith('/decide')) {
          decideCalls += 1;
          expect(request.body, contains('"action":"approve"'));
          expect(request.body, contains('"assigned_role":"admin"'));
          return http.Response(
            '''
{
  "id": "r1",
  "user_id": "u1",
  "user_email": "sinrol@example.com",
  "user_full_name": "Sin Rol",
  "user_role": "admin",
  "requested_role": "guide",
  "status": "approved",
  "decided_role": "admin",
  "decided_by": "admin1",
  "decided_at": "2026-01-02T00:00:00Z",
  "note": null,
  "version": 1,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-02T00:00:00Z",
  "deleted_at": null
}
''',
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.method == 'GET') {
          listCalls += 1;
          return http.Response(
            '[]',
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('unexpected', 500);
      });

      final controller = RoleRequestsController(apiClient: client);
      final decided = await controller.decide(
        requestId: 'r1',
        action: 'approve',
        assignedRole: 'admin',
      );

      expect(decided.status, 'approved');
      expect(decided.decidedRole, 'admin');
      expect(decideCalls, 1);
      expect(listCalls, 1);
      expect(controller.state, RoleRequestsLoadState.empty);
      controller.dispose();
    });
  });
}
