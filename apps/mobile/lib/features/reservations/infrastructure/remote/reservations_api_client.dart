import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:mobile_domain/src/gen/reservation_create.dart';
import 'package:mobile_domain/src/gen/reservation_rules.dart' as gen;

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

  Future<List<ReservationListItemDto>> listReservations({
    bool includeDeleted = false,
    bool? assistantDisabled,
  }) async {
    final params = <String>[];
    if (includeDeleted) params.add('include_deleted=true');
    if (assistantDisabled != null) {
      params.add('assistant_disabled=$assistantDisabled');
    }
    final path = params.isEmpty
        ? '/reservations'
        : '/reservations?${params.join('&')}';
    final response = await _authorizedRequest(
      method: 'GET',
      path: path,
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

  /// Creates a reservation manually. Online-only.
  Future<ReservationDetailDto> createReservation(
    ReservationCreate payload,
  ) async {
    final body = Map<String, dynamic>.from(payload.toJson())
      ..removeWhere((_, value) => value == null);
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/reservations',
      body: body,
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  Future<ReservationDetailDto> updateReservation({
    required String reservationId,
    bool? assistantDisabled,
  }) async {
    final response = await _authorizedRequest(
      method: 'PATCH',
      path: '/reservations/$reservationId',
      body: {
        if (assistantDisabled != null) 'assistant_disabled': assistantDisabled,
      },
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

  /// Approves payment without a proof document (cash, external, etc.).
  /// Returns the full updated reservation detail.
  Future<ReservationDetailDto> approvePaymentWithoutProof({
    required String reservationId,
    String? note,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/reservations/$reservationId/approve-payment',
      body: {
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
    String? startTime,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/reservations/$reservationId/confirm',
      body: {
        if (notes != null) 'notes': notes,
        if (startTime != null) 'start_time': startTime,
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

  /// Soft-deletes a reservation (sets deleted_at).
  Future<ReservationDetailDto> deleteReservation({
    required String reservationId,
  }) async {
    final response = await _authorizedRequest(
      method: 'DELETE',
      path: '/reservations/$reservationId',
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  /// Restores a soft-deleted reservation.
  Future<ReservationDetailDto> restoreReservation({
    required String reservationId,
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/reservations/$reservationId/restore',
    );
    final data = _decodeBody(response.body);
    return ReservationDetailDto.fromJson(data);
  }

  Future<gen.ReservationRules> getReservationRules() async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/config/reservation-rules',  // backend: /api/v1/config/reservation-rules
    );
    final data = _decodeBody(response.body);
    return gen.ReservationRules.fromJson(data);
  }

  Future<List<ReservationTimelineEntryDto>> getReservationTimeline(
    String reservationId,
  ) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/reservations/$reservationId/timeline',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw ReservationsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en timeline de reserva.',
      );
    }
    return decoded
        .map((item) {
          if (item is! Map) {
            throw ReservationsApiFailure(
              code: 'network.invalid_payload',
              message: 'Payload inválido en timeline de reserva.',
            );
          }
          return ReservationTimelineEntryDto.fromJson(
            Map<String, dynamic>.from(item),
          );
        })
        .toList(growable: false);
  }

  Future<List<ReservationProviderItemDto>> getReservationProviders(
    String reservationId,
  ) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/reservations/$reservationId/providers',
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw ReservationsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en proveedores de reserva.',
      );
    }
    return decoded
        .map((item) => ReservationProviderItemDto.fromJson(
              Map<String, dynamic>.from(item as Map),
            ))
        .toList(growable: false);
  }

  Future<List<ProviderCatalogItemDto>> listProviders({
    String? query,
    bool isActive = true,
  }) async {
    final queryParams = <String, String>{
      if (isActive) 'is_active': 'true',
      if (query != null && query.trim().isNotEmpty) 'q': query.trim(),
    };
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/providers',
      queryParameters: queryParams.isEmpty ? null : queryParams,
    );
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw ReservationsApiFailure(
        code: 'network.invalid_payload',
        message: 'Payload inválido en catálogo de proveedores.',
      );
    }
    return decoded
        .map((item) => ProviderCatalogItemDto.fromJson(
              Map<String, dynamic>.from(item as Map),
            ))
        .toList(growable: false);
  }

  Future<ReservationProviderItemDto> createReservationProvider({
    required String reservationId,
    required String providerId,
    String? serviceLabel,
    String? notes,
    String status = 'pending',
  }) async {
    final response = await _authorizedRequest(
      method: 'POST',
      path: '/reservations/$reservationId/providers',
      body: {
        'provider_id': providerId,
        if (serviceLabel != null) 'service_label': serviceLabel,
        if (notes != null) 'notes': notes,
        'status': status,
      },
    );
    return ReservationProviderItemDto.fromJson(
      Map<String, dynamic>.from(_decodeBody(response.body) as Map),
    );
  }

  Future<ReservationProviderItemDto> updateReservationProvider({
    required String reservationId,
    required String reservationProviderId,
    String? serviceLabel,
    String? notes,
    String? status,
  }) async {
    final response = await _authorizedRequest(
      method: 'PATCH',
      path: '/reservations/$reservationId/providers/$reservationProviderId',
      body: {
        if (serviceLabel != null) 'service_label': serviceLabel,
        if (notes != null) 'notes': notes,
        if (status != null) 'status': status,
      },
    );
    return ReservationProviderItemDto.fromJson(
      Map<String, dynamic>.from(_decodeBody(response.body) as Map),
    );
  }

  Future<void> deleteReservationProvider({
    required String reservationId,
    required String reservationProviderId,
  }) async {
    await _authorizedRequest(
      method: 'DELETE',
      path: '/reservations/$reservationId/providers/$reservationProviderId',
    );
  }

  Future<void> createLogNote({
    required String reservationId,
    required String notes,
    List<Map<String, dynamic>> photos = const [],
  }) async {
    await _authorizedRequest(
      method: 'POST',
      path: '/logs',
      body: {
        'reservation_id': reservationId,
        'event_type': 'note',
        'happened_at': DateTime.now().toUtc().toIso8601String(),
        'notes': notes,
        if (photos.isNotEmpty) 'photos': photos,
      },
    );
  }

  Future<void> updateLogNote({
    required String logId,
    required String notes,
    List<Map<String, dynamic>>? photos,
  }) async {
    await _authorizedRequest(
      method: 'PATCH',
      path: '/logs/$logId',
      body: {
        'notes': notes,
        if (photos != null) 'photos': photos,
      },
    );
  }

  Future<ReservationLogNoteDetailDto> getLogNote(String logId) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/logs/$logId',
    );
    final data = _decodeBody(response.body);
    return ReservationLogNoteDetailDto.fromJson(data);
  }

  Future<ReservationLogPhotoUploadDto> uploadLogPhoto({
    required String reservationId,
    required Uint8List bytes,
    required String filename,
    required String contentType,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw ReservationsApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesión válida para consultar reservas.',
      );
    }

    final uri = Uri.parse(
      '$_baseUrl/logs/photos/upload?reservation_id=$reservationId',
    );
    final request = http.MultipartRequest('POST', uri)
      ..headers[HttpHeaders.authorizationHeader] = 'Bearer $accessToken'
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          bytes,
          filename: filename,
          contentType: MediaType.parse(contentType),
        ),
      );

    http.StreamedResponse streamed;
    try {
      streamed = await request.send().timeout(const Duration(seconds: 12));
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
    }

    final response = await http.Response.fromStream(streamed);
    if (response.statusCode == 401 && retryAuth) {
      final refreshed = await _refreshSession();
      if (refreshed) {
        return uploadLogPhoto(
          reservationId: reservationId,
          bytes: bytes,
          filename: filename,
          contentType: contentType,
          retryAuth: false,
        );
      }
    }
    _throwIfError(response);
    final data = _decodeBody(response.body);
    return ReservationLogPhotoUploadDto.fromJson(data);
  }

  Future<Uint8List> downloadLogPhoto({
    required String logId,
    required int photoIndex,
  }) async {
    final response = await _authorizedRequest(
      method: 'GET',
      path: '/logs/$logId/photos/$photoIndex/download',
    );
    return response.bodyBytes;
  }

  Future<void> deleteLogEntry(String logId) async {
    await _authorizedRequest(
      method: 'DELETE',
      path: '/logs/$logId',
    );
  }

  Future<http.Response> _authorizedRequest({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    Map<String, String>? queryParameters,
    bool retryAuth = true,
  }) async {
    final accessToken = await _readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      throw ReservationsApiFailure(
        code: 'auth.session_expired',
        message: 'No hay sesión válida para consultar reservas.',
      );
    }
    var uri = Uri.parse('$_baseUrl$path');
    if (queryParameters != null && queryParameters.isNotEmpty) {
      uri = uri.replace(queryParameters: queryParameters);
    }
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
          queryParameters: queryParameters,
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
