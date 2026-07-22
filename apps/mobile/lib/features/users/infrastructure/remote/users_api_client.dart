import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'package:mobile/features/users/domain/user_models.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_error.dart';

class UsersApiClient {
  UsersApiClient({
    required String baseUrl,
    required Future<String?> Function() readAccessToken,
    required Future<bool> Function() refreshSession,
    http.Client? httpClient,
  })  : _baseUrl = baseUrl,
        _readAccessToken = readAccessToken,
        _refreshSession = refreshSession,
        _http = httpClient ?? http.Client();

  final String _baseUrl;
  final Future<String?> Function() _readAccessToken;
  final Future<bool> Function() _refreshSession;
  final http.Client _http;

  Future<List<UserRecord>> listUsers({int limit = 200}) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/users?limit=$limit',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw UsersApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido al listar usuarios.',
      );
    }
    return decoded
        .map(
          (item) => UserRecord.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList(growable: false);
  }

  Future<UserRecord> createUser({
    required String email,
    required String fullName,
    required String password,
    required String role,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/users',
      body: {
        'email': email,
        'full_name': fullName,
        'password': password,
        'role': role,
      },
    );
    return UserRecord.fromJson(_decodeBody(response.body));
  }

  Future<UserRecord> updateUser(
    String userId, {
    String? fullName,
    String? role,
    bool? isActive,
  }) async {
    final body = <String, dynamic>{
      if (fullName != null) 'full_name': fullName,
      if (role != null) 'role': role,
      if (isActive != null) 'is_active': isActive,
    };
    final response = await _authorizedRequest(
      method: 'PATCH',
      path: '/users/$userId',
      body: body,
    );
    return UserRecord.fromJson(_decodeBody(response.body));
  }

  Future<void> deactivateUser(String userId) async {
    await _authorizedRequest(method: 'DELETE', path: '/users/$userId');
  }

  Future<List<RoleRequestRecord>> listRoleRequests({
    String status = 'pending',
    int limit = 200,
  }) async {
    final query = <String, String>{
      'status': status,
      'limit': '$limit',
    };
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/role-requests?${Uri(queryParameters: query).query}',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw UsersApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido al listar solicitudes.',
      );
    }
    return decoded
        .map(
          (item) =>
              RoleRequestRecord.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList(growable: false);
  }

  Future<RoleRequestRecord?> getMyRoleRequest() async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/role-requests/me',
    );
    if (response.body.trim().isEmpty || response.body.trim() == 'null') {
      return null;
    }
    final decoded = jsonDecode(response.body);
    if (decoded == null) return null;
    if (decoded is! Map) {
      throw UsersApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido al consultar solicitud.',
      );
    }
    return RoleRequestRecord.fromJson(Map<String, dynamic>.from(decoded));
  }

  Future<RoleRequestRecord> createMyRoleRequest(String requestedRole) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/role-requests',
      body: {'requested_role': requestedRole},
    );
    return RoleRequestRecord.fromJson(_decodeBody(response.body));
  }

  Future<RoleRequestRecord> decideRoleRequest({
    required String requestId,
    required String action,
    String? assignedRole,
    String? note,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/role-requests/$requestId/decide',
      body: {
        'action': action,
        if (assignedRole != null) 'assigned_role': assignedRole,
        if (note != null) 'note': note,
      },
    );
    return RoleRequestRecord.fromJson(_decodeBody(response.body));
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw UsersApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesión válida.',
      );
    }
    final uri = Uri.parse('$_baseUrl$path');
    final response = await _execute(() {
      switch (method) {
        case 'GET':
          return _http.get(uri, headers: _headers(accessToken));
        case 'POST':
          return _http.post(
            uri,
            headers: _headers(accessToken),
            body: body != null ? jsonEncode(body) : null,
          );
        case 'PATCH':
          return _http.patch(
            uri,
            headers: _headers(accessToken),
            body: body != null ? jsonEncode(body) : null,
          );
        case 'DELETE':
          return _http.delete(uri, headers: _headers(accessToken));
        default:
          throw UnsupportedError('Método no soportado: $method');
      }
    });
    if (response.statusCode == 401 && retryAuth) {
      final refreshed = await _refreshSession();
      if (refreshed) {
        return _authorizedRequest(
          method: method,
          path: path,
          body: body,
          retryAuth: false,
        );
      }
    }
    _throwIfError(response);
    return response;
  }

  Map<String, String> _headers(String accessToken) {
    return {
      HttpHeaders.contentTypeHeader: 'application/json',
      HttpHeaders.authorizationHeader: 'Bearer $accessToken',
    };
  }

  Future<http.Response> _execute(
    Future<http.Response> Function() block,
  ) async {
    try {
      return await block().timeout(const Duration(seconds: 12));
    } on TimeoutException {
      throw UsersApiFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado.',
      );
    } on SocketException {
      throw UsersApiFailure(
        code: 'network.unavailable',
        message: 'No hay conexión con el servidor.',
      );
    } on HttpException {
      throw UsersApiFailure(
        code: 'network.http_error',
        message: 'Error de red.',
      );
    } on FormatException {
      throw UsersApiFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor.',
      );
    }
  }

  Map<String, dynamic> _decodeBody(String body) {
    if (body.trim().isEmpty) {
      throw UsersApiFailure(
        code: 'network.invalid_payload',
        message: 'Respuesta vacía del servidor.',
      );
    }
    final decoded = jsonDecode(body);
    if (decoded is! Map) {
      throw UsersApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido.',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw UsersApiFailure(
      code: error.$1,
      message: error.$2,
      statusCode: response.statusCode,
    );
  }

  (String, String) _decodeApiError(String body) {
    if (body.trim().isEmpty) {
      return ('common.error', 'Error inesperado');
    }
    try {
      final decoded = jsonDecode(body);
      if (decoded is! Map<String, dynamic>) {
        return ('common.error', 'Error inesperado');
      }
      return (
        (decoded['code'] as String?) ??
            (decoded['error_code'] as String?) ??
            'common.error',
        (decoded['message'] as String?) ??
            (decoded['error'] as String?) ??
            'Error inesperado',
      );
    } catch (_) {
      return ('common.error', 'Error inesperado');
    }
  }
}
