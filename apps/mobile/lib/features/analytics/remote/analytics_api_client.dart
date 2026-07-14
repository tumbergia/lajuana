import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import 'analytics_api_error.dart';

class AnalyticsApiClient {
  AnalyticsApiClient({
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

  Future<Map<String, dynamic>> fetchLeads({bool forceRefresh = false}) async {
    final qs = forceRefresh ? '?force_refresh=true' : '';
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/analytics/leads$qs',
    );
    return _decodeBody(response.body);
  }

  Future<Map<String, dynamic>> fetchLeadsPreferences() async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/analytics/leads/preferences',
    );
    return _decodeBody(response.body);
  }

  Future<Map<String, dynamic>> updateLeadsPreferences({
    required List<String> pinnedLeadIds,
    required List<String> excludedLeadIds,
  }) async {
    final response = await _authorizedRequest(
      method: 'PUT',
      path: '/analytics/leads/preferences',
      body: {
        'pinned_lead_ids': pinnedLeadIds,
        'excluded_lead_ids': excludedLeadIds,
      },
    );
    return _decodeBody(response.body);
  }

  Future<Uint8List> downloadExport({String? leadId}) async {
    final qs = leadId != null ? '?lead_id=$leadId' : '';
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/analytics/leads/export$qs',
    );
    return response.bodyBytes;
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw AnalyticsApiFailure(
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
        case 'PUT':
          return _http.put(
            uri,
            headers: _headers(accessToken),
            body: body != null ? jsonEncode(body) : null,
          );
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
      throw AnalyticsApiFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado.',
      );
    } on SocketException {
      throw AnalyticsApiFailure(
        code: 'network.unavailable',
        message: 'No hay conexión con el servidor.',
      );
    } on HttpException {
      throw AnalyticsApiFailure(
        code: 'network.http_error',
        message: 'Error de red.',
      );
    } on FormatException {
      throw AnalyticsApiFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor.',
      );
    }
  }

  Map<String, dynamic> _decodeBody(String body) {
    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw AnalyticsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido.',
      );
    }
    return decoded;
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw AnalyticsApiFailure(
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

  void dispose() {
    _http.close();
  }
}
