import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import 'reservation_dtos.dart';
import 'reservations_api_error.dart';

class ReservationsApiClient {
  ReservationsApiClient({
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

  Future<List<ReservationListItemDto>> listReservations() async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/reservations',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw ReservationsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido',
      );
    }
    return decoded
        .map((item) {
          if (item is! Map) {
            throw ReservationsApiFailure(
              code: 'network.invalid_payload',
              message: 'Payload inválido',
            );
          }
          return ReservationListItemDto.fromJson(
            Map<String, dynamic>.from(item),
          );
        })
        .toList(growable: false);
  }

  Future<ReservationDetailDto> getReservationById(
    String reservationId,
  ) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/reservations/$reservationId',
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  /// Downloads a payment proof file via streaming.
  /// Returns the raw bytes; caller can interpret based on content type.
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/payment-proofs/$paymentProofId/download',
    );
    return response.bodyBytes;
  }

  /// Approves a payment proof. Returns the full updated reservation detail.
  Future<ReservationDetailDto> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/payment-proofs/$paymentProofId/approve',
      body: {
        'confirmation_token': 'APPROVE_PAYMENT',
        if (note != null) 'note': note,
      },
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  /// Un-verifies (undoes) a previously verified payment proof.
  /// Returns the full updated reservation detail.
  Future<ReservationDetailDto> unverifyPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/payment-proofs/$paymentProofId/unverify',
      body: {
        'confirmation_token': 'UNVERIFY_PAYMENT',
        if (note != null) 'note': note,
      },
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  /// Un-rejects (undoes) a previously rejected payment proof.
  /// Returns the full updated reservation detail.
  Future<ReservationDetailDto> unrejectPaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/payment-proofs/$paymentProofId/unreject',
      body: {
        'confirmation_token': 'UNREJECT_PAYMENT',
        if (note != null) 'note': note,
      },
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  /// Rejects a payment proof with a mandatory reason.
  /// Returns the full updated reservation detail.
  Future<ReservationDetailDto> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/payment-proofs/$paymentProofId/reject',
      body: {
        'confirmation_token': 'REJECT_PAYMENT',
        'reason': reason,
      },
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  /// Confirms a reservation. Returns the full updated reservation detail.
  /// Online-only, admin-only.
  Future<ReservationDetailDto> confirmReservation({
    required String reservationId,
    String? notes,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/reservations/$reservationId/confirm',
      body: {
        if (notes != null) 'notes': notes,
      },
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  /// Cancels a reservation. Returns the full updated reservation detail.
  /// Online-only, admin-only.
  Future<ReservationDetailDto> cancelReservation({
    required String reservationId,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/reservations/$reservationId/cancel',
      body: {},
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw ReservationsApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesión válida para consultar reservas.',
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
      throw ReservationsApiFailure(
        code: 'network.timeout',
        message: 'Tiempo de espera agotado al consultar reservas.',
      );
    } on SocketException {
      throw ReservationsApiFailure(
        code: 'network.unavailable',
        message: 'No hay conexión con el servidor.',
      );
    } on HttpException {
      throw ReservationsApiFailure(
        code: 'network.http_error',
        message: 'Error de red al consultar reservas.',
      );
    } on FormatException {
      throw ReservationsApiFailure(
        code: 'network.invalid_response',
        message: 'Respuesta inválida del servidor.',
      );
    }
  }

  Map<String, dynamic> _decodeBody(String body) {
    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw ReservationsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en respuesta de reservas.',
      );
    }
    return decoded;
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final error = _decodeApiError(response.body);
    throw ReservationsApiFailure(
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
