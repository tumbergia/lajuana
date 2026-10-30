import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:mobile_domain/src/providers/provider_list_item.dart';

import 'providers_api_error.dart';

class ProvidersApiClient {
  ProvidersApiClient({
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

  Future<List<ProviderListItem>> listProviders({
    int limit = 1000,
    bool includeDeleted = false,
  }) async {
    final query = <String, String>{
      'limit': '$limit',
      if (includeDeleted) 'include_deleted': 'true',
    };
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/providers?${Uri(queryParameters: query).query}',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw ProvidersApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return decoded
        .map(
          (item) =>
              ProviderListItem.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList(growable: false);
  }

  Future<ProviderListItem> getProviderById(String providerId) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/providers/$providerId',
    );
    return ProviderListItem.fromJson(_decodeBody(response.body));
  }

  Future<ProviderListItem> createProvider(Map<String, dynamic> payload) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/providers',
      body: payload,
    );
    return ProviderListItem.fromJson(_decodeBody(response.body));
  }

  Future<ProviderListItem> updateProvider(
    String providerId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _authorizedRequest(
      method: 'PATCH',
      path: '/providers/$providerId',
      body: payload,
    );
    return ProviderListItem.fromJson(_decodeBody(response.body));
  }

  Future<void> deactivateProvider(String providerId) async {
    await _authorizedRequest(method: 'DELETE', path: '/providers/$providerId');
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw ProvidersApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesión válida para consultar proveedores.',
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
      throw ProvidersApiFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado al consultar proveedores.',
      );
    } on SocketException {
      throw ProvidersApiFailure(
        code: 'network.unavailable',
        message: 'No hay conexión con el servidor.',
      );
    } on HttpException {
      throw ProvidersApiFailure(
        code: 'network.http_error',
        message: 'Error de red al consultar proveedores.',
      );
    } on FormatException {
      throw ProvidersApiFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor.',
      );
    }
  }

  Map<String, dynamic> _decodeBody(String body) {
    if (body.trim().isEmpty) {
      throw ProvidersApiFailure(
        code: 'network.invalid_payload',
        message: 'Respuesta vacía del servidor.',
      );
    }
    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw ProvidersApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en respuesta de proveedores.',
      );
    }
    return decoded;
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw ProvidersApiFailure(
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
