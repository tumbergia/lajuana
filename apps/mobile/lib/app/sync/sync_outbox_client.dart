import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Falla de red o de autorizacion al hablar con los endpoints `/sync`.
///
/// Los codigos `network.*` se tratan como "sin conexion" (la operacion queda
/// pendiente y se reintenta luego); el resto se propaga.
class SyncApiFailure implements Exception {
  SyncApiFailure({
    required this.code,
    required this.message,
    this.statusCode,
  });

  final String code;
  final String message;
  final int? statusCode;

  bool get isNetwork => code.startsWith('network.');

  @override
  String toString() => message;
}

/// Cliente HTTP del outbox compartido. Generalizacion de `CatalogsSyncApi`
/// para que asignaciones/saddles reusen el mismo protocolo `/sync`.
class SyncOutboxClient {
  SyncOutboxClient({
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

  Future<Map<String, dynamic>> getSyncBootstrap() async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/sync/bootstrap',
    );
    return _decodeBody(response.body);
  }

  Future<Map<String, dynamic>> postSyncPull({
    required Map<String, dynamic> body,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/sync/pull',
      body: body,
    );
    return _decodeBody(response.body);
  }

  Future<Map<String, dynamic>> postSyncPush({
    required Map<String, dynamic> body,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/sync/push',
      body: body,
    );
    return _decodeBody(response.body);
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw SyncApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesion valida para sincronizar.',
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
            body: body == null ? null : jsonEncode(body),
          );
        default:
          throw UnsupportedError('Metodo no soportado: $method');
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
      throw SyncApiFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado en sincronizacion.',
      );
    } on SocketException {
      throw SyncApiFailure(
        code: 'network.unavailable',
        message: 'No hay conexion con el servidor.',
      );
    } on HttpException {
      throw SyncApiFailure(
        code: 'network.http_error',
        message: 'Error de red al sincronizar.',
      );
    } on FormatException {
      throw SyncApiFailure(
        code: 'network.invalid_response',
        message: 'Respuesta invalida del servidor.',
      );
    }
  }

  Map<String, dynamic> _decodeBody(String body) {
    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw SyncApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload invalido en respuesta de sync.',
      );
    }
    return decoded;
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw SyncApiFailure(
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
