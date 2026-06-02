import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class AssignmentsApiClient {
  AssignmentsApiClient({
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

  /// GET /api/v1/assignments/board/{reservationId}
  Future<Map<String, dynamic>> getBoard(String reservationId) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/assignments/board/$reservationId',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// POST /api/v1/assignments
  Future<Map<String, dynamic>> create(Map<String, dynamic> body) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/assignments',
      body: body,
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// GET /api/v1/assignments/{id}
  Future<Map<String, dynamic>> getById(String id) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/assignments/$id',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// PATCH /api/v1/assignments/{id}
  Future<Map<String, dynamic>> update(String id, Map<String, dynamic> body) async {
    final response = await _authorizedRequest(
      method: 'PATCH',
      path: '/assignments/$id',
      body: body,
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// POST /api/v1/assignments/{id}/finalize
  Future<Map<String, dynamic>> finalize(String id) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/assignments/$id/finalize',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// POST /api/v1/assignments/{id}/unfinalize
  Future<Map<String, dynamic>> unfinalize(String id) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/assignments/$id/unfinalize',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// DELETE /api/v1/assignments/{id}
  Future<Map<String, dynamic>> remove(String id) async {
    final response = await _authorizedRequest(
      method: 'DELETE',
      path: '/assignments/$id',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// POST /api/v1/assignments/{id}/replace
  Future<Map<String, dynamic>> replace(String id, Map<String, dynamic> body) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/assignments/$id/replace',
      body: body,
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// POST /api/v1/assignments/reservation/{reservationId}/finalize-all
  Future<Map<String, dynamic>> finalizeAll(
    String reservationId, {
    String? notes,
  }) async {
    final body = <String, dynamic>{};
    if (notes != null && notes.isNotEmpty) {
      body['notes'] = notes;
    }
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/assignments/reservation/$reservationId/finalize-all',
      body: body,
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// POST /api/v1/assignments/reservation/{reservationId}/unfinalize-all
  Future<Map<String, dynamic>> unfinalizeAll(
    String reservationId, {
    String? notes,
  }) async {
    final body = <String, dynamic>{};
    if (notes != null && notes.isNotEmpty) {
      body['notes'] = notes;
    }
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/assignments/reservation/$reservationId/unfinalize-all',
      body: body,
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// POST /api/v1/assignments/reservation/{reservationId}/batch
  Future<Map<String, dynamic>> batchUpdate({
    required String reservationId,
    required List<Map<String, dynamic>> assignments,
    required List<String> removals,
    String? notes,
  }) async {
    final body = <String, dynamic>{
      'assignments': assignments,
      'removals': removals,
    };
    if (notes != null && notes.isNotEmpty) {
      body['notes'] = notes;
    }
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/assignments/reservation/$reservationId/batch',
      body: body,
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  /// POST /api/v1/logs — create a service log entry
  Future<Map<String, dynamic>> createLog(Map<String, dynamic> body) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/logs',
      body: body,
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw AssignmentsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return Map<String, dynamic>.from(decoded);
  }

  // ── Auth layer ──

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
  }) async {
    final token = await _readAccessToken();
    final uri = Uri.parse('$_baseUrl$path');

    final headers = <String, String>{
      HttpHeaders.contentTypeHeader: 'application/json',
    };
    if (token != null) {
      headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
    }

    late http.Response response;
    try {
      response = await _http.send(
        http.Request(method.toUpperCase(), uri)
          ..headers.addAll(headers)
          ..body = body != null ? jsonEncode(body) : '',
      ).then((streamed) => http.Response.fromStream(streamed));
    } catch (e) {
      throw AssignmentsApiFailure(
        code: 'network.unreachable',
        message: 'No se pudo conectar con el servidor: $e',
      );
    }

    if (response.statusCode == 401) {
      final refreshed = await _refreshSession();
      if (refreshed) {
        final newToken = await _readAccessToken();
        if (newToken != null) {
          headers[HttpHeaders.authorizationHeader] = 'Bearer $newToken';
        }
        response = await _http.send(
          http.Request(method.toUpperCase(), uri)
            ..headers.addAll(headers)
            ..body = body != null ? jsonEncode(body) : '',
        ).then((streamed) => http.Response.fromStream(streamed));
      } else {
        throw AssignmentsApiFailure(
          code: 'auth.session_expired',
          message: 'Sesión expirada. Inicie sesión nuevamente.',
        );
      }
    }

    if (response.statusCode >= 400) {
      final decoded = _tryDecode(response.body);
      throw AssignmentsApiFailure(
        code: decoded['code'] as String? ?? 'network.error',
        message: decoded['message'] as String? ?? 'Error HTTP ${response.statusCode}',
      );
    }

    return response;
  }

  Map<String, dynamic> _tryDecode(String body) {
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map) return Map<String, dynamic>.from(decoded);
    } catch (_) {}
    return {};
  }
}

class AssignmentsApiFailure implements Exception {
  AssignmentsApiFailure({required this.code, required this.message});

  final String code;
  final String message;

  @override
  String toString() => 'AssignmentsApiFailure($code): $message';
}
