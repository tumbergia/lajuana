import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'package:mobile_domain/src/saddles/saddle_list_item.dart';
import 'saddles_api_error.dart';

class SaddlesApiClient {
  SaddlesApiClient({
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

  Future<List<SaddleListItem>> listSaddles({
    bool includeDeleted = false,
  }) async {
    final queryParams = <String, String>{};
    if (includeDeleted) {
      queryParams['include_deleted'] = 'true';
    }
    final path =
        '/saddles${queryParams.isNotEmpty ? '?${Uri(queryParameters: queryParams).query}' : ''}';
    final response = await _authorizedRequest(method: 'GET', path: path);
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw SaddlesApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return decoded
        .map((item) {
          if (item is! Map) {
            throw SaddlesApiFailure(
              code: 'network.invalid_payload',
              message: 'Payload inválido',
            );
          }
          return SaddleListItem.fromJson(Map<String, dynamic>.from(item));
        })
        .toList(growable: false);
  }

  Future<SaddleListItem> getSaddleById(String saddleId) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/saddles/$saddleId',
    );
    final data = _decodeBody(response.body);
    return SaddleListItem.fromJson(data);
  }

  Future<SaddleListItem> createSaddle(Map<String, dynamic> payload) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/saddles',
      body: payload,
    );
    final data = _decodeBody(response.body);
    return SaddleListItem.fromJson(data);
  }

  Future<SaddleListItem> deleteSaddle(String saddleId) async {
    final response = await _authorizedRequest(
      method: 'DELETE',
      path: '/saddles/$saddleId',
    );
    final data = _decodeBody(response.body);
    return SaddleListItem.fromJson(data);
  }

  Future<SaddleListItem> restoreSaddle(String saddleId) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/saddles/$saddleId/restore',
    );
    final data = _decodeBody(response.body);
    return SaddleListItem.fromJson(data);
  }

  Future<SaddleListItem> updateSaddle(
    String saddleId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _authorizedRequest(
      method: 'PATCH',
      path: '/saddles/$saddleId',
      body: payload,
    );
    final data = _decodeBody(response.body);
    return SaddleListItem.fromJson(data);
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw SaddlesApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesión válida para consultar sillas.',
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

  Future<http.Response> _execute(Future<http.Response> Function() block) async {
    try {
      return await block().timeout(const Duration(seconds: 12));
    } on TimeoutException {
      throw SaddlesApiFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado al consultar sillas.',
      );
    } on SocketException {
      throw SaddlesApiFailure(
        code: 'network.unavailable',
        message: 'No hay conexión con el servidor.',
      );
    } on HttpException {
      throw SaddlesApiFailure(
        code: 'network.http_error',
        message: 'Error de red al consultar sillas.',
      );
    } on FormatException {
      throw SaddlesApiFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor.',
      );
    }
  }

  Map<String, dynamic> _decodeBody(String body) {
    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw SaddlesApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en respuesta de sillas.',
      );
    }
    return decoded;
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw SaddlesApiFailure(
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
