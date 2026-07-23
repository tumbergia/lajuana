import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'equine_dtos.dart';
import 'equines_api_error.dart';

/// Cliente HTTP para el endpoint /api/v1/equines.
/// Sigue el mismo patrón que [ReservationsApiClient].
class EquinesApiClient {
  EquinesApiClient({
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

  Future<List<EquineDto>> listEquines({
    String? operationalStatus,
    bool includeDeleted = false,
  }) async {
    final queryParams = <String, String>{};
    if (operationalStatus != null) {
      queryParams['operational_status'] = operationalStatus;
    }
    // Por defecto solo equinos activos.
    if (!includeDeleted) {
      queryParams['is_active'] = 'true';
    }
    if (includeDeleted) {
      queryParams['include_deleted'] = 'true';
    }
    final queryString = queryParams.isEmpty
        ? ''
        : '?${Uri(queryParameters: queryParams).query}';
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/equines/list$queryString',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw EquinesApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en lista de equinos.',
      );
    }
    return decoded
        .map((item) {
          if (item is! Map) {
            throw EquinesApiFailure(
              code: 'network.invalid_payload',
              message: 'Payload inválido en lista de equinos.',
            );
          }
          return EquineDto.fromJson(Map<String, dynamic>.from(item));
        })
        .toList(growable: false);
  }

  Future<EquineDto> getEquineById(String equineId) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/equines/$equineId',
    );
    final data = _decodeBody(response.body);
    return EquineDto.fromJson(data);
  }

  Future<EquineDto> createEquine(Map<String, dynamic> data) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/equines',
      body: data,
    );
    return EquineDto.fromJson(_decodeBody(response.body));
  }

  Future<EquineDto> updateEquine(
    String equineId,
    Map<String, dynamic> data,
  ) async {
    final response = await _authorizedRequest(
      method: 'PATCH',
      path: '/equines/$equineId',
      body: data,
    );
    return EquineDto.fromJson(_decodeBody(response.body));
  }

  Future<EquineEventDto> createEquineEvent(
    String equineId,
    Map<String, dynamic> data,
  ) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/equines/$equineId/events',
      body: data,
    );
    return EquineEventDto.fromJson(_decodeBody(response.body));
  }

  Future<List<EquineTimelineEntryDto>> getEquineTimeline(
    String equineId,
  ) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/equines/$equineId/timeline',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw EquinesApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en timeline de equino.',
      );
    }
    return decoded
        .map((item) {
          if (item is! Map) {
            throw EquinesApiFailure(
              code: 'network.invalid_payload',
              message: 'Payload inválido en timeline de equino.',
            );
          }
          return EquineTimelineEntryDto.fromJson(
            Map<String, dynamic>.from(item),
          );
        })
        .toList(growable: false);
  }

  Future<EquineDto> deleteEquine(String equineId) async {
    final response = await _authorizedRequest(
      method: 'DELETE',
      path: '/equines/$equineId',
    );
    return EquineDto.fromJson(_decodeBody(response.body));
  }

  Future<EquineDto> restoreEquine(String equineId) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/equines/$equineId/restore',
    );
    return EquineDto.fromJson(_decodeBody(response.body));
  }

  Future<List<EquineDto>> listAvailableForReservation(
    String reservationId,
  ) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/equines/available-for-reservation/$reservationId',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw EquinesApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en equinos disponibles.',
      );
    }
    return decoded
        .map((item) {
          if (item is! Map) {
            throw EquinesApiFailure(
              code: 'network.invalid_payload',
              message: 'Payload inválido en equinos disponibles.',
            );
          }
          return EquineDto.fromJson(Map<String, dynamic>.from(item));
        })
        .toList(growable: false);
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw EquinesApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesión válida para consultar equinos.',
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
      throw EquinesApiFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado al consultar equinos.',
      );
    } on SocketException {
      throw EquinesApiFailure(
        code: 'network.unavailable',
        message: 'No hay conexión con el servidor.',
      );
    } on HttpException {
      throw EquinesApiFailure(
        code: 'network.http_error',
        message: 'Error de red al consultar equinos.',
      );
    } on FormatException {
      throw EquinesApiFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor.',
      );
    }
  }

  Map<String, dynamic> _decodeBody(String body) {
    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw EquinesApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en respuesta de equinos.',
      );
    }
    return decoded;
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw EquinesApiFailure(
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
