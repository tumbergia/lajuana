import 'dart:convert';
import 'dart:io';
import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../../domain/auth_models.dart';
import 'auth_dtos.dart';

class AuthApiClient {
  AuthApiClient({http.Client? httpClient, String? baseUrl})
    : _http = httpClient ?? http.Client(),
      _baseUrl = baseUrl ?? _resolveDefaultBaseUrl();

  static const String _envBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  final http.Client _http;
  final String _baseUrl;

  static String _resolveDefaultBaseUrl() {
    if (_envBaseUrl.isNotEmpty) {
      if (!_isWebUnsafeHost(_envBaseUrl)) return _envBaseUrl;
      debugPrint(
        'Ignoring API_BASE_URL=$_envBaseUrl on web. '
        'Use localhost/127.0.0.1 for browser runs.',
      );
    }
    if (kIsWeb) return 'http://localhost:8000/api/v1';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return 'http://127.0.0.1:8000/api/v1';
  }

  static bool _isWebUnsafeHost(String url) {
    if (!kIsWeb) return false;
    final host = Uri.tryParse(url)?.host.toLowerCase();
    return host == '10.0.2.2' || host == '127.0.0.1.nip.io';
  }

  Future<TokenDto> login({
    required String email,
    required String password,
  }) async {
    final response = await _post(
      '/auth/login',
      body: {'email': email, 'password': password},
    );
    final data = _decodeBody(response.body);
    return TokenDto.fromJson(data);
  }

  Future<TokenDto> refresh({required String refreshToken}) async {
    final uri = Uri.parse(
      '$_baseUrl/auth/refresh?refresh_token=${Uri.encodeQueryComponent(refreshToken)}',
    );
    final response = await _execute(() => _http.post(uri));
    _throwIfError(response);
    final data = _decodeBody(response.body);
    return TokenDto.fromJson(data);
  }

  Future<void> logout({required String accessToken}) async {
    await _post('/auth/logout', bearer: accessToken);
  }

  Future<UserDto> me({required String accessToken}) async {
    final response = await _get('/auth/me', bearer: accessToken);
    final data = _decodeBody(response.body);
    return UserDto.fromJson(data);
  }

  Future<UserDto> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    final response = await _post(
      '/auth/register',
      body: {'full_name': fullName, 'email': email, 'password': password},
    );
    final data = _decodeBody(response.body);
    return UserDto.fromJson(data);
  }

  Future<void> changePassword({
    required String accessToken,
    required String currentPassword,
    required String newPassword,
  }) async {
    await _post(
      '/auth/change-password',
      bearer: accessToken,
      body: {'current_password': currentPassword, 'new_password': newPassword},
    );
  }

  Future<http.Response> _get(String path, {String? bearer}) async {
    final uri = Uri.parse('$_baseUrl$path');
    final response = await _execute(() {
      return _http.get(uri, headers: _headers(bearer: bearer));
    });
    _throwIfError(response);
    return response;
  }

  Future<http.Response> _post(
    String path, {
    String? bearer,
    Map<String, dynamic>? body,
  }) async {
    final uri = Uri.parse('$_baseUrl$path');
    final response = await _execute(() {
      return _http.post(
        uri,
        headers: _headers(bearer: bearer),
        body: body == null ? null : jsonEncode(body),
      );
    });
    _throwIfError(response);
    return response;
  }

  Map<String, String> _headers({String? bearer}) {
    return {
      HttpHeaders.contentTypeHeader: 'application/json',
      if (bearer != null) HttpHeaders.authorizationHeader: 'Bearer $bearer',
    };
  }

  Future<http.Response> _execute(Future<http.Response> Function() block) async {
    try {
      return await block().timeout(const Duration(seconds: 8));
    } on TimeoutException {
      throw AuthFailure(
        code: 'network.timeout',
        message: 'La solicitud tardó demasiado',
      );
    } on SocketException {
      throw AuthFailure(code: 'network.unavailable', message: 'Sin conexión');
    } on HttpException {
      throw AuthFailure(code: 'network.http_error', message: 'Error de red');
    } on FormatException {
      throw AuthFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor',
      );
    }
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw AuthFailure(
      code: error.code,
      message: error.message,
      statusCode: response.statusCode,
    );
  }

  Map<String, dynamic> _decodeBody(String body) {
    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw AuthFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return decoded;
  }

  ApiErrorDto _decodeApiError(String body) {
    if (body.trim().isEmpty) {
      return ApiErrorDto(code: 'common.error', message: 'Error inesperado');
    }
    try {
      final decoded = jsonDecode(body);
      if (decoded is! Map<String, dynamic>) {
        if (decoded is String && decoded.trim().isNotEmpty) {
          return ApiErrorDto(code: 'common.error', message: decoded);
        }
        return ApiErrorDto(code: 'common.error', message: 'Error inesperado');
      }
      final map = decoded;
      final detail = map['detail'];
      final detailMessage = _extractDetailMessage(detail);
      return ApiErrorDto(
        code:
            (map['code'] as String?) ??
            (map['error_code'] as String?) ??
            'common.error',
        message:
            (map['message'] as String?) ??
            (map['error'] as String?) ??
            detailMessage ??
            'Error inesperado',
      );
    } catch (_) {
      return ApiErrorDto(code: 'common.error', message: 'Error inesperado');
    }
  }

  String? _extractDetailMessage(dynamic detail) {
    if (detail is String && detail.trim().isNotEmpty) return detail;
    if (detail is List && detail.isNotEmpty) {
      final first = detail.first;
      if (first is Map<String, dynamic>) {
        final msg = first['msg'];
        if (msg is String && msg.trim().isNotEmpty) return msg;
      }
      if (first is String && first.trim().isNotEmpty) return first;
    }
    return null;
  }
}
