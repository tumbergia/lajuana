import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:mobile/features/configuration/domain/la_juana_configuration.dart';

class ConfigurationApiFailure implements Exception {
  const ConfigurationApiFailure(this.message, {this.statusCode});
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

class ConfigurationApiClient {
  ConfigurationApiClient({
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

  static String _errorMessage(Object? decoded) {
    if (decoded is! Map) {
      return 'No se pudo guardar la configuración.';
    }
    final message = decoded['message'] as String?;
    final details = decoded['details'];
    if (details is Map) {
      final fields = details['fields'];
      if (fields is List && fields.isNotEmpty) {
        final first = fields.first;
        if (first is Map) {
          final reason = first['msg'] as String? ?? first['reason'] as String?;
          if (reason != null && reason.isNotEmpty) {
            return reason;
          }
        }
      }
    }
    return message ?? 'No se pudo guardar la configuración.';
  }

  Future<AiConfiguration> getAi() async =>
      AiConfiguration.fromJson(await _request('GET', '/config/ai'));
  Future<AiConfiguration> updateAi(Map<String, dynamic> body) async =>
      AiConfiguration.fromJson(
        await _request('PATCH', '/config/ai', body: body),
      );
  Future<PaymentConfiguration> getPayments() async =>
      PaymentConfiguration.fromJson(
        await _request('GET', '/config/payment-methods'),
      );
  Future<PaymentConfiguration> updatePayments(
    Map<String, dynamic> body,
  ) async => PaymentConfiguration.fromJson(
    await _request('PATCH', '/config/payment-methods', body: body),
  );
  Future<BusinessLocationConfiguration> getLocation() async =>
      BusinessLocationConfiguration.fromJson(
        await _request('GET', '/config/business-location'),
      );
  Future<BusinessLocationConfiguration> updateLocation(
    Map<String, dynamic> body,
  ) async => BusinessLocationConfiguration.fromJson(
    await _request('PATCH', '/config/business-location', body: body),
  );

  Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool retry = true,
  }) async {
    final token = await _readAccessToken();
    if (token == null || token.isEmpty)
      throw const ConfigurationApiFailure('La sesión expiró.');
    final uri = Uri.parse('$_baseUrl$path');
    try {
      final headers = {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.authorizationHeader: 'Bearer $token',
      };
      final response =
          await (method == 'GET'
                  ? _http.get(uri, headers: headers)
                  : _http.patch(uri, headers: headers, body: jsonEncode(body)))
              .timeout(const Duration(seconds: 15));
      if (response.statusCode == 401 && retry && await _refreshSession())
        return _request(method, path, body: body, retry: false);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final decoded = response.body.isEmpty
            ? null
            : jsonDecode(response.body);
        throw ConfigurationApiFailure(
          _errorMessage(decoded),
          statusCode: response.statusCode,
        );
      }
      final decoded = jsonDecode(response.body);
      if (decoded is! Map)
        throw const ConfigurationApiFailure('Respuesta inválida del servidor.');
      return Map<String, dynamic>.from(decoded);
    } on TimeoutException {
      throw const ConfigurationApiFailure(
        'El servidor tardó demasiado en responder.',
      );
    } on SocketException {
      throw const ConfigurationApiFailure('No hay conexión con el servidor.');
    } on FormatException {
      throw const ConfigurationApiFailure('Respuesta inválida del servidor.');
    }
  }
}
