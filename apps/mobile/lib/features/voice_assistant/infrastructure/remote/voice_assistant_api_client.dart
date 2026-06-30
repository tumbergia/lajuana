import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../domain/assistant_ask_result.dart';
import 'voice_assistant_api_error.dart';

class VoiceAssistantApiClient {
  VoiceAssistantApiClient({
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

  Future<AssistantAskResult> ask({
    required String message,
    String? conversationId,
  }) async {
    final body = <String, dynamic>{
      'message': message,
      if (conversationId != null && conversationId.isNotEmpty)
        'conversation_id': conversationId,
    };
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/admin/ask',
      body: body,
    );
    return AssistantAskResult.fromJson(_decodeBody(response.body));
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw VoiceAssistantApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesión válida para consultar el asistente.',
      );
    }
    final uri = Uri.parse('$_baseUrl$path');
    final response = await _execute(() {
      switch (method) {
        case 'POST':
          return _http.post(
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

  Future<http.Response> _execute(
    Future<http.Response> Function() block,
  ) async {
    try {
      return await block().timeout(const Duration(seconds: 60));
    } on TimeoutException {
      throw VoiceAssistantApiFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado al consultar el asistente.',
      );
    } on SocketException {
      throw VoiceAssistantApiFailure(
        code: 'network.unavailable',
        message: 'No hay conexión con el servidor.',
      );
    } on HttpException {
      throw VoiceAssistantApiFailure(
        code: 'network.http_error',
        message: 'Error de red al consultar el asistente.',
      );
    } on FormatException {
      throw VoiceAssistantApiFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor.',
      );
    }
  }

  Map<String, dynamic> _decodeBody(String body) {
    if (body.trim().isEmpty) {
      throw VoiceAssistantApiFailure(
        code: 'network.invalid_payload',
        message: 'Respuesta vacía del servidor.',
      );
    }
    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw VoiceAssistantApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en respuesta del asistente.',
      );
    }
    return decoded;
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw VoiceAssistantApiFailure(
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
